"""RAMon Chatbot FastAPI Application.

This module defines the FastAPI application with clean architecture,
wiring together all layers: core, domain, adapters, API, and infrastructure.
"""
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncShallowPostgresSaver

from chatbot import ChatbotBuilder
from chatbot.adapters import PostgresProductRepository

from src.adapters import PostgresProductCatalog
from src.api.routes import chat_router, root_router, websocket_router
from src.core.config import AppConfig, AuthConfig, ConfigError
from src.infrastructure.database import create_db_pool

logger = logging.getLogger("ramon.server")

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for initializing and cleaning up resources."""
    # Load configuration
    try:
        app_config = AppConfig.from_env()
        auth_config = AuthConfig.from_env()
    except ConfigError as exc:
        logger.critical("Failed to load configuration: %s", exc)
        raise

    # Initialize database pool
    db_pool = create_db_pool(app_config.database_url)
    await db_pool.open()

    # Build services
    app.state.chatbot_service = (
        ChatbotBuilder()
        .with_openai(
            api_key=app_config.openai_api_key,
            model=app_config.openai_model,
            temperature=app_config.openai_temperature,
        )
        .with_tavily(api_key=app_config.tavily_api_key)
        .with_checkpointer(AsyncShallowPostgresSaver(db_pool))
        .with_product_repository(PostgresProductRepository(db_pool))
        .build()
    )
    app.state.product_catalog = PostgresProductCatalog(db_pool)
    app.state.auth_config = auth_config

    yield

    # Cleanup
    await db_pool.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RAMon Chatbot",
        description="AI-powered hardware store assistant",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Register routers
    app.include_router(root_router)
    app.include_router(chat_router)
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
