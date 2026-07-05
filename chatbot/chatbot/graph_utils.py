"""Utility functions for graph visualization."""
from pathlib import Path
from typing import Union

from chatbot.application.service import ChatbotService


def generate_graph_image(service: ChatbotService) -> bytes:
    """Generate a PNG image of the chatbot's LangGraph workflow.

    Args:
        service: An initialized ChatbotService instance

    Returns:
        PNG image bytes
    """
    graph = service.compiled_graph.get_graph()
    return graph.draw_mermaid_png()


def save_graph_image(
    service: ChatbotService,
    output_path: Union[str, Path],
) -> Path:
    """Generate and save a PNG image of the chatbot's LangGraph workflow.

    Args:
        service: An initialized ChatbotService instance
        output_path: Path where the image should be saved

    Returns:
        Path to the saved image file
    """
    output_path = Path(output_path)
    png_bytes = generate_graph_image(service)

    with open(output_path, "wb") as f:
        f.write(png_bytes)

    return output_path
