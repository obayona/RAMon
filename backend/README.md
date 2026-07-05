# RAMon Backend

FastAPI server that wraps the RAMon chatbot library for web deployment. It provides
a WebSocket API for real-time streaming conversations and bundles a lightweight demo UI.

## Prerequisites

- Python 3.10+
- The `chatbot` package (shared library)

## Getting Started

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

### 3. Configure environment variables

Create a `.env` file or create a symlink to the root `.env`:

```bash
ln -s ../.env .env
```

Check ../.env.example

### 4. Run the server

```bash
uvicorn server:app --reload --port 8080
```

The root route (`/`) serves the demo UI. Open `http://localhost:8080` to start a session.

### 5. Access API documentation

Open `http://localhost:8080/docs` to see HTTP endpoint documentation.

## WebSocket Protocol

Clients connect to `/ws?chat_id=<session-id>` and exchange UTF-8 text frames.

**Request format:**
```json
{
  "message": "User input text",
  "current_product_id": "optional-catalog-id"
}
```

If a plain string is sent, the server treats it as the `message` with no current product.

**Response format:**
Responses are streamed JSON snapshots containing assistant tokens and any structured
`ui_payload` entries for product carousels.
