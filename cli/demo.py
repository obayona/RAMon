#!/usr/bin/env python3
"""RAMon Chatbot CLI Demo

This script demonstrates the usage of the ChatbotService for testing
and development purposes. It runs predefined test scenarios to verify
the chatbot's functionality.

Usage:
    python demo.py

Requires:
    - Install chatbot package: pip install -e ../chatbot
    - .env file with required environment variables
"""
import asyncio
import os
import uuid
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

from chatbot import ChatbotBuilder, Product
from chatbot.adapters import PostgresProductRepository

load_dotenv()


async def run_demo():
    """Run demonstration scenarios for the chatbot."""
    print("Initializing chatbot...")

    db_pool = AsyncConnectionPool(
        conninfo=os.environ.get('DATABASE_URL'),
        min_size=2,
        max_size=10,
        open=False,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row
        }
    )
    await db_pool.open()

    try:
        # Build chatbot using the new builder pattern
        # MemorySaver is used by default (great for CLI/testing)
        bot = (
            ChatbotBuilder()
            .with_openai(
                api_key=os.environ.get('OPENAI_API_KEY'),
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=float(os.environ.get("OPENAI_TEMPERATURE", "0.0")),
            )
            .with_tavily(api_key=os.environ.get('TAVILY_API_KEY'))
            .with_product_repository(PostgresProductRepository(db_pool))
            .build()
        )
        print("Chatbot initialized successfully!\n")

        # Generate unique session ID for this demo run
        session_id = str(uuid.uuid4())[:8]

        # ---- Test 1: Product Recommendation ----
        user_query = "Necesito un KIT DE CAMARA EZVIZ, no importa el precio"
        print("=" * 72)
        print("TEST 1 - Product Recommendation")
        print(f"User: {user_query}")
        print("current_product: None")
        print("=" * 72)

        result = await bot.ainvoke(user_query, chat_id=f"demo-{session_id}-test-1")
        _print_result(result)

        # ---- Test 2: Technical Compatibility ----
        user_query = "Es esta memoria RAM compatible con mi tarjeta ASUS Prime B450M?"
        print("\n" + "=" * 72)
        print("TEST 2 - Technical Compatibility")
        print(f"User: {user_query}")
        print("current_product: Corsair Vengeance LPX 16GB DDR4")
        print("=" * 72)

        current_ram: Product = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "sku": "ram-001",
            "name": "Corsair Vengeance LPX (2x8GB) DDR4",
            "description": "DDR4 3200MHz CL16, 1.35V, Intel XMP 2.0, black PCB, dual-channel desktop memory kit",
            "categories": "Memory",
            "price": 49.99,
            "stock": 10,
        }

        result = await bot.ainvoke(user_query, current_product=current_ram, chat_id=f"demo-{session_id}-test-2")
        _print_result(result)

    finally:
        await db_pool.close()


def _print_result(result):
    """Pretty print the chatbot result."""
    messages = result.get("messages", [])
    recommendations = result.get("recommendations", [])

    print("\n--- Response ---")
    for msg in messages:
        role = type(msg).__name__
        content = getattr(msg, "content", "")
        if content:
            print(f"[{role}]: {content}")

    if recommendations:
        print("\n--- Product Recommendations ---")
        for i, product in enumerate(recommendations, 1):
            print(f"  {i}. {product.get('name', 'N/A')} - ${product.get('price', 0):.2f}")
            print(f"     {product.get('description', '')[:80]}...")


if __name__ == "__main__":
    asyncio.run(run_demo())
