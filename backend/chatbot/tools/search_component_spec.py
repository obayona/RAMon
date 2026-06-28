import json

from langchain_core.tools import tool
from langchain_tavily import TavilySearch


def make_search_component_spec(tavily_client: TavilySearch):
    """Create the ``search_component_spec`` tool with a pre-configured Tavily client.
    """

    @tool
    def search_component_spec(component_model: str) -> str:
        """Fetch technical specifications for an external hardware component from the web.

        Use when a user asks about compatibility with their own motherboard, CPU, GPU
        or other component so that you can compare specs against the product they are
        currently viewing on the store."""
        try:
            results = tavily_client.invoke(
                {"query": f"{component_model} technical specifications specs"}
            )
            return json.dumps(results, indent=2)
        except Exception as exc:
            return (
                f"[Web search unavailable: {exc}]\n\n"
                f"For component '{component_model}' verify:\n"
                f"- Motherboard: chipset, socket, memory standard (DDR4/DDR5), "
                f"max frequency, form factor\n"
                f"- CPU: socket, supported memory type, TDP, generation\n"
                f"- GPU: PCIe version, physical dimensions, power connector\n"
                f"Always consult the manufacturer's official page for definitive specs."
            )

    return search_component_spec
