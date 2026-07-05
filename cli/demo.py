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
from dotenv import load_dotenv

load_dotenv()

from chatbot import Product, create_chatbot


def run_demo():
    """Run demonstration scenarios for the chatbot."""
    print("Initializing chatbot...")
    bot = create_chatbot()
    print("Chatbot initialized successfully!\n")

    # ---- Test 1: Product Recommendation ----
    user_query = "Necesito un KIT DE CAMARA EZVIZ, no importa el precio"
    print("=" * 72)
    print("TEST 1 - Product Recommendation")
    print(f"User: {user_query}")
    print("current_product: None")
    print("=" * 72)

    result = bot.invoke(user_query, chat_id="demo-test-1")
    _print_result(result)

    # ---- Test 2: Technical Compatibility ----
    user_query = "Es esta memoria RAM compatible con mi tarjeta ASUS Prime B450M?"
    print("\n" + "=" * 72)
    print("TEST 2 - Technical Compatibility")
    print(f"User: {user_query}")
    print("current_product: Corsair Vengeance LPX 16GB DDR4")
    print("=" * 72)

    current_ram: Product = {
        "id": "ram-001",
        "name": "Corsair Vengeance LPX 16GB (2x8GB) DDR4",
        "description": "DDR4 3200MHz CL16, 1.35V, Intel XMP 2.0, black PCB, dual-channel desktop memory kit",
        "price": 49.99,
        "url": "/products/ram-001",
    }

    result = bot.invoke(user_query, current_product=current_ram, chat_id="demo-test-2")
    _print_result(result)


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
    run_demo()
