"""RAMon Chatbot FastAPI Application.

This module defines the FastAPI application with clean architecture,
wiring together all layers: core, domain, adapters, API, and infrastructure.
"""
from __future__ import annotations

import structlog
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncShallowPostgresSaver

from chatbot import ChatbotBuilder
from chatbot.adapters import PostgresProductRepository

from src.adapters import PostgresProductCatalog
from src.adapters.sync_queue import PostgresSyncEnqueuer
from src.api.middleware import RequestIDMiddleware
from src.api.routes import chat_router, root_router, sync_router, websocket_router
from src.core.config import ConfigError, config, load_settings
from src.core.logging import configure_logging
from src.infrastructure.database import create_db_pool

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for initializing and cleaning up resources."""
    # Load all settings first
    try:
        settings = load_settings()
    except ConfigError as exc:
        # Logging not configured yet — use structlog default
        log = structlog.get_logger("ramon.server")
        log.critical("config.load.failed", error=str(exc))
        raise

    # Configure logging from settings
    configure_logging(
        level=config("logging.level"),
        fmt=config("logging.fmt"),
        log_dir=config("logging.log_dir"),
    )
    log = structlog.get_logger("ramon.server")
    log.info(
        "config.loaded",
        openai_model=config("app.openai_model"),
        openai_temperature=config("app.openai_temperature"),
    )

    # Initialize database pool
    db_pool = create_db_pool(config("app.database_url"))
    await db_pool.open()
    log.info("database.connected")

    # Build services
    app.state.chatbot_service = (
        ChatbotBuilder()
        .with_openai(
            api_key=config("app.openai_api_key"),
            model=config("app.openai_model"),
            temperature=config("app.openai_temperature"),
        )
        .with_tavily(api_key=config("app.tavily_api_key"))
        .with_checkpointer(AsyncShallowPostgresSaver(db_pool))
        .with_product_repository(PostgresProductRepository(db_pool))
        .build()
    )
    app.state.product_catalog = PostgresProductCatalog(db_pool)
    app.state.sync_enqueuer = PostgresSyncEnqueuer(db_pool)
    app.state.auth_config = config("auth")
    log.info("services.built")

    yield

    # Cleanup
    log.info("shutdown")
    await db_pool.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RAMon Chatbot",
        description="AI-powered hardware store assistant",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Request ID middleware — must be added before routes
    app.add_middleware(RequestIDMiddleware)

    # Register routers
    app.include_router(root_router)
    app.include_router(chat_router)
    app.include_router(sync_router)
    app.include_router(websocket_router)

    # CORS middleware - allow all origins
    # Must be added after routes for Starlette middleware stack order
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )

    return app


# Application instance for uvicorn
app = create_app()
