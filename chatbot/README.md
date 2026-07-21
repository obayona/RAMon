# RAMon Chatbot

Shared chatbot library for RAMon — a technical assistance chatbot for computer e-commerce.

This package provides the core chatbot functionality using LangGraph, OpenAI, pgvector,
and Tavily. It is designed to be used by both the backend server and CLI tools.

## Architecture

The package follows clean architecture principles with three layers:

```
chatbot/
├── domain/           # Core domain models (Product, AgentState)
├── application/      # Business logic (ChatbotService, graph workflow)
└── adapters/         # External adapters (OpenAI embeddings, PostgreSQL catalog)
```

### LangGraph Workflow

The chatbot is implemented as a LangGraph state machine:

![LangGraph flow](graph.png)

**Nodes:**
- `chatbot` — Routes messages through OpenAI with system prompt and product context
- `tools` — Executes LangChain tools (product search, web search)
- `process_recommendations` — LLM-powered relevance evaluation that filters bad results

**Flow:**
1. User message → `chatbot` decides whether to call tools
2. If `recommend_products` is called → tool uses `Command(goto="process_recommendations")` to:
   - Update state with `product_query` and `recommendations`
   - Route directly to `process_recommendations` node
3. `process_recommendations` evaluates if products match the query
4. Relevant products are embedded in response as `<products>[...]</products>` markers
5. Irrelevant or empty results: LLM explains what's missing (no hardcoded responses)
6. If `search_component_spec` is called → results flow back to `chatbot` for natural response

## Installation

Install in editable mode from another project (e.g., backend or cli):

```bash
pip install -e ../chatbot
```

Or add to `requirements.txt`:

```
-e ../chatbot
```

## Quick Start

The only way to build the service is through `ChatbotBuilder`. It uses a
fluent/chainable API so you can configure every dependency step by step:

```python
from chatbot import ChatbotBuilder

chatbot = (
    ChatbotBuilder()
    .with_openai(api_key="sk-...")
    .with_tavily(api_key="tvly-...")
    .with_product_repository(PostgresProductRepository(pool))
    .build()
)
```

## API Reference

### ChatbotBuilder

`ChatbotBuilder` is the single entry point for creating a `ChatbotService`. Every
method returns `self`, so calls can be chained. Three configuration steps are
**required** before calling `build()`:

| Method | Required | Description |
|---|---|---|
| `with_openai(api_key, ...)` | **Yes** | Configure OpenAI API key, model, and embedding model. |
| `with_tavily(api_key, ...)` | **Yes** | Configure Tavily web-search API key. |
| `with_product_repository(repo)` | **Yes** | Provide a `ProductRepository` implementation. |

Optional configuration:

| Method | Default | Description |
|---|---|---|
| `with_checkpointer(checkpointer)` | `MemorySaver` (in-memory) | Use a persistent checkpointer (e.g., `AsyncShallowPostgresSaver`) for production. |
| `with_embedding_service(service)` | `OpenAIEmbeddingService` | Override the embedding service (useful for testing). |
| `with_openai_client(client, ...)` | — | Pass a pre-configured `OpenAI` client instance. |
| `with_tavily_client(client)` | — | Pass a pre-configured `TavilySearch` client instance. |


#### Usage with Postgres checkpointer

```python
from psycopg_pool import AsyncConnectionPool
from chatbot import ChatbotBuilder
from chatbot.adapters import PostgresProductRepository
from langgraph.checkpoint.postgres.aio import AsyncShallowPostgresSaver

db_pool = AsyncConnectionPool(
    conninfo=DB_URL,
    min_size=2,
    max_size=10,
    open=False,
    kwargs={
        "autocommit": True,
        "row_factory": dict_row
    }
)
await db_pool.open()

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
```

### ChatbotService

```python
# Synchronous invocation
result = chatbot.invoke(
    message="Find me a 4K monitor",
    current_product=None,  # Optional product context
    chat_id="session-123",
)

# Async streaming
async for chunk in chatbot.stream(message="...", chat_id="..."):
    print(chunk)

# Get chat history
history = await chatbot.get_chat_history("session-123")
```

### Tools

The chatbot uses two LangChain tools (registered automatically via `build_tools`):

#### `recommend_products`

Semantic product search using embeddings. Accepts a natural language query and
optional `min_price` / `max_price` filters. Returns the top 3 matching products
as JSON.

```python
@tool
async def recommend_products(
    query: str,
    min_price: float | None = None,
    max_price: float | None = None,
) -> str
```

#### `search_component_spec`

Fetches technical specifications for an external hardware component (motherboard,
CPU, GPU, etc.) from the web via Tavily. Useful when the user asks about
compatibility with hardware they already own.

```python
@tool
async def search_component_spec(component_model: str) -> str
```

### Graph Visualization

Generate a PNG image of the LangGraph workflow:

```python
from chatbot import save_graph_image

save_graph_image(chatbot, "graph.png")
```

Or get the raw bytes:

```python
from chatbot import generate_graph_image

png_bytes = generate_graph_image(chatbot)
```
