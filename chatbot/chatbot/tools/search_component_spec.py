import json

import structlog
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

logger = structlog.get_logger("ramon.chatbot.tools")


def make_search_component_spec(tavily_client: TavilySearch):
    @tool
    async def search_component_spec(component_model: str) -> str:
        """Fetch technical specifications or system requirements from the web.

        Use this tool whenever the user asks whether a product is compatible with something
        they already own or want to run. This includes:
        - Hardware compatibility: motherboard, CPU, GPU, RAM, etc. (e.g. "is this CPU compatible
          with my motherboard X79?")
        - Software/model requirements: AI models, operating systems, games, etc.
          (e.g. "can this laptop run Gemma 4?", "will this PC handle Windows 11?")

        Pass a descriptive search query. For hardware, use the component model name
        (e.g. "X79M-S"). For software or AI models, include "system requirements" in the
        query (e.g. "Gemma 4 AI model system requirements GPU RAM CPU").

        Always use the results to compare against the current product's specs before
        answering. Never ask the user for requirements you can look up yourself.
        """
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
