#!/usr/bin/env python3
"""Generate an image of the chatbot graph.

This script creates a visual representation of the LangGraph workflow
and saves it as graph.png.

Usage:
    python show_graph.py [output_path]

Arguments:
    output_path  Optional path for the output image (default: ../chatbot/graph.png)
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from chatbot import create_chatbot, save_graph_image


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "../chatbot/graph.png"
    output_path = Path(output_path)

    print("Initializing chatbot...")
    bot = create_chatbot()

    print("Generating graph image...")
    saved_path = save_graph_image(bot, output_path)

    print(f"Graph saved to {saved_path.resolve()}")


if __name__ == "__main__":
    main()
