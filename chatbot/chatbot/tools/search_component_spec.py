import json

import structlog
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

logger = structlog.get_logger("ramon.chatbot.tools")


def make_search_component_spec(tavily_client: TavilySearch):
    @tool
    async def search_component_spec(component_model: str) -> str:
        """Fetch technical specifications for an external hardware component from the web.

        Use when a user asks about compatibility with their own motherboard, CPU, GPU
        or other component so that you can compare specs against the product they are
        currently viewing on the store."""
        logger.debug("search_component_spec.query", component_model=component_model)

        try:
            results = await tavily_client.ainvoke(
                {"query": f"{component_model} technical specifications specs"}
            )
            logger.debug(
                "search_component_spec.results",
                component_model=component_model,
            )
            return json.dumps(results, indent=2)
        except Exception as exc:
            logger.warning(
                "search_component_spec.failed",
                component_model=component_model,
                error=str(exc),
            )
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
