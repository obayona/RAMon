# RAMon Backend

FastAPI server that wraps the RAMon chatbot library for web deployment. It provides
a WebSocket API for real-time streaming conversations and bundles a lightweight demo UI.

## Configure environment variables

Create a `.env` file using `.env.example` as reference:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required variables:
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` - PostgreSQL connection settings
- `OPENAI_API_KEY` - OpenAI API key
- `TAVILY_API_KEY` - Tavily API key
- `APP_KEY` - Secret key for JWT signing
- `GUEST_USER` - Basic auth username
- `GUEST_PASSWORD` - Basic auth password


## Quick Start with Docker (Recommended)

The easiest way to run the backend is with Docker Compose, which handles PostgreSQL, migrations, and the FastAPI server.

> **Note:** Docker Compose files are located in the `deploy/` folder at the repository root.
> All docker compose commands should be run from that directory.
> You should create on `deploy` a symblink of the `backend/.env` file

### 1. Start the development stack

```bash
cd ../deploy
docker compose up --watch
```

This will:
- Start PostgreSQL with pgvector extension
- Run database migrations automatically
- Start the FastAPI server with hot-reload
- Watch for file changes and sync them to the container

The server will be available at `http://localhost:8000`.

### 2. Load product fixtures

```bash
cd ../deploy
docker compose run --rm fixtures-load
```

### 3. Stop the stack

```bash
cd ../deploy
docker compose down        # Stop containers
docker compose down -v     # Stop and remove volumes (fresh start)
```

## Local Development (Without Docker)

### Prerequisites

- Python 3.10+
- PostgreSQL 16+ with pgvector extension
- The `chatbot` package (shared library)


### 1. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

This installs the `chatbot` package in editable mode along with FastAPI and other server dependencies.

### 3. Set up the database

Run migrations (includes products table and LangGraph checkpointer tables):

```bash
yoyo apply --database postgresql+psycopg://user:pass@localhost/dbname
```

### 5. Run the server

```bash
uvicorn src.main:app --reload --port 8000
```

The root route (`/`) serves the demo UI. Open `http://localhost:8000` to start a session.

## Database Migrations

Migrations are managed with [yoyo-migrations](https://ollycope.com/software/yoyo/latest/).

The `yoyo.ini` file configures the migrations directory.

### Check migration status

```bash
yoyo list --database postgresql+psycopg://user:pass@localhost/dbname
```

### Apply pending migrations

```bash
yoyo apply --database postgresql+psycopg://user:pass@localhost/dbname
```

### Rollback the last migration

```bash
yoyo rollback --database postgresql+psycopg://user:pass@localhost/dbname
```

### Create a new migration

```bash
yoyo new -m "add_new_feature"
```

Or manually create a new Python file in `migrations/` following the naming convention:

```
migrations/
├── 0001_initial_schema.py
├── 0002_add_new_feature.py
└── ...
```

## Project Structure

```
backend/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── core/                # Configuration
│   │   └── config.py
│   ├── domain/              # Business entities & ports
│   │   ├── models.py
│   │   └── ports.py
│   ├── adapters/            # Port implementations
│   │   └── product_catalog.py
│   ├── api/                 # API layer
│   │   ├── auth.py
│   │   ├── dependencies.py
│   │   ├── middleware.py
│   │   └── routes/
│   │       ├── root.py
│   │       ├── chat.py
│   │       └── websocket.py
│   └── infrastructure/      # External services
│       └── database.py
├── migrations/              # Yoyo database migrations
├── fixtures/                # small database dump
├── yoyo.ini                 # Yoyo configuration
├── index.html               # Demo UI
└── Dockerfile
```

## API Documentation

Open `http://localhost:8000/docs` to see the interactive API documentation.

## WebSocket Protocol

Clients connect to `/ws?chat_id=<session-id>&token=<jwt-token>` and exchange UTF-8 text frames.

**Request format:**
```json
{
  "message": "User input text",
  "current_product_id": "product_sku"
}
```

If a plain string is sent, the server treats it as the `message` with no current product.

**Response format:**
Responses are streamed JSON snapshots containing assistant tokens and any structured
`ui_payload` entries for product carousels.

## Logging

RAMon uses [structlog](https://www.structlog.org/) for structured, contextual logging.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Minimum log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_FORMAT` | `text` | Output format: `text` (human-readable) or `json` (structured) |
| `LOG_DIR` | `""` (stdout) | Directory for log files. Empty = stdout only (dev mode) |

### Development (stdout)

Logs go to stdout in human-readable text format. View them with:

```bash
docker compose logs -f backend
```

### Production (files + logrotate)

Set `LOG_FORMAT=json` and `LOG_DIR=/var/log/ramon`. Logs are written to:

- `/var/log/ramon/api.log` — API server, WebSocket, sync, and chatbot logs
- `/var/log/ramon/worker.log` — Background sync worker

Rotation is handled by logrotate (daily, 14 days retention, compressed).

### Log channels

| Logger | Purpose |
|---|---|
| `ramon.server` | App lifecycle (startup, shutdown, config) |
| `ramon.api` | HTTP request/response middleware |
| `ramon.websocket` | WebSocket connect/disconnect/errors (correlated by `chat_id`) |
| `ramon.sync` | Sync enqueuer |
| `ramon.chatbot.*` | Chatbot library (service, graph, tools, adapters) |
| `ramon.sync.worker` | Background sync worker |

### Request tracing

Every HTTP request gets a UUID4 `request_id` (returned as `X-Request-ID` header).
WebSocket connections are traced by `chat_id`. Both are included in all log records
via structlog's context variables.

### Integrating Sentry

The logging pipeline is designed for easy extensibility. To add Sentry:

1. Install: `pip install sentry-sdk[fastapi]`
2. In `src/core/logging.py`, add a `SentryHandler` to the stdlib logging config:

```python
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.ERROR,        # Send errors to Sentry
    event_level=logging.ERROR,  # Only create Sentry events for ERROR+
)
sentry_sdk.init(dsn="...", integrations=[sentry_logging])
```

Or add a structlog processor for more control over what gets sent.

No changes needed to individual logger call sites — the processor/handler chain
is the extension point.
