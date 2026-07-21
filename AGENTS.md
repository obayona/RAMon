# AGENTS.md - RAMon Monorepo Guidelines

## Project Overview

RAMon is an AI-powered chatbot for computer hardware e-commerce sites. The monorepo contains:

- **backend/** — FastAPI API server (Python 3.10+, async)
- **chatbot/** — LangGraph chatbot library (Python package, installed editable)
- **frontend/** — React 19 chat widget (TypeScript, Vite 8, Tailwind CSS 4)
- **cli/** — Manual demo/test scripts
- **deploy/** — Docker Compose + nginx configs
- **integrations/** — WordPress plugin (PHP)
- **tools/** — Database utilities and web scraper

---

## Build, Lint & Test Commands

### Frontend (pnpm)

```bash
cd frontend
pnpm install              # Install dependencies
pnpm dev                  # Dev server with HMR (Express + Vite middleware)
pnpm build                # TS compile + Vite widget build → dist-widget/
pnpm start                # Production server
pnpm lint                 # ESLint (src/**/*.ts,tsx)
```

### Backend (pip + uvicorn)

```bash
cd backend
pip install -r requirements.txt   # Installs deps + editable chatbot
uvicorn src.main:app --reload     # Dev server (port 8000)
```

### Chatbot Package

```bash
cd chatbot
pip install -e .                  # Editable install
```

### CLI Testing

```bash
cd cli
pip install -r requirements.txt
python demo.py                    # Runs 2 manual test scenarios
```

### Database Migrations (yoyo)

```bash
yoyo apply --database postgresql+psycopg://user:pass@host:5432/dbname
yoyo rollback
yoyo list
```

### Docker (dev)

```bash
cd deploy
docker compose up --watch              # PG + backend with hot-reload
docker compose run --rm fixtures-load  # Load product fixtures
```

### Testing

There is no formal test suite yet. Use `cli/demo.py` for manual validation.
When adding tests, use **pytest** for Python and **vitest** for frontend.

---

## Code Style — Python (backend/, chatbot/)

### Architecture

Clean architecture with layers: `core/` → `domain/` → `adapters/` → `api/` → `infrastructure/`.
Domain logic uses `Protocol` for dependency injection (`typing.Protocol` with `@runtime_checkable`).
Builder pattern for complex initialization (`ChatbotBuilder` with method chaining).

### Formatting

- No formatter configured (Black/Ruff not present). Follow existing style.
- 4-space indentation.
- Max line length ~100 chars (informal).

### Imports

Order: stdlib → third-party → local packages. Group with blank lines.

```python
import json
import logging
from dataclasses import dataclass

from fastapi import APIRouter, Depends
from langgraph.checkpoint.base import BaseCheckpointSaver

from chatbot.application.service import ChatbotService
from src.core.config import AppConfig
```

Use `from __future__ import annotations` at top of file when using modern type syntax.
Use absolute imports from `src.*` in backend, relative or absolute `chatbot.*` in chatbot package.

### Types

- Use `@dataclass(frozen=True, slots=True)` for immutable config/state objects.
- Use `TypedDict` for structured state dicts (e.g., `AgentState`, `ChatbotState`).
- Use `Protocol` for abstract interfaces (ports).
- Use `str | None` union syntax (Python 3.10+), not `Optional[str]`.
- Type hint all public function signatures and return types.

### Naming Conventions

- `snake_case` for functions, variables, module names.
- `PascalCase` for classes, exceptions.
- Private module helpers prefixed with `_` (e.g., `_build_database_url`).
- Loggers: `structlog.get_logger("ramon.<module>")` (e.g., `ramon.server`, `ramon.websocket`).
- Router variable always named `router` in route modules.

### Logging

Use [structlog](https://www.structlog.org/) throughout. The library emits
log records; the host application configures handlers.

- **Backend**: `structlog.get_logger("ramon.<module>")` — configure via
  `configure_logging()` in `src/core/logging.py`.
- **Chatbot**: Same pattern, but log at DEBUG level only. Never call
  `structlog.configure()` from the library.

Log events use `dot.separated` names (e.g., `ws.connected`, `worker.batch.completed`).
Context is passed as keyword arguments: `logger.info("event", key=value)`.

Use `structlog.contextvars.bind_contextvars()` for request-scoped context
(request_id, chat_id). The `merge_contextvars` processor picks these up
automatically.

### Docstrings

Every public module, class, and function must have a docstring.
Use Google-style docstrings:

```python
def with_openai(self, api_key: str, *, model: str = "gpt-4o-mini") -> ChatbotBuilder:
    """Configure OpenAI using an API key.

    Args:
        api_key: OpenAI API key.
        model: Chat model to use (default: gpt-4o-mini).

    Returns:
        Self for method chaining.
    """
```

### Error Handling

- Define custom exceptions in `core/` or `domain/` (e.g., `ConfigError`, `ChatNotFoundError`).
- Use `try/except` with specific exception types; re-raise as custom exceptions.
- Config loading: `require()` helper raises `ConfigError` with descriptive messages.
- WebSocket handler: catch broad `Exception` with `logger.exception()`, then gracefully close.
- Log errors with `logger.exception()` for full traceback, `logger.error()` for simple messages.

### Async

All I/O is async-first: `async def`, `AsyncConnectionPool`, `AsyncShallowPostgresSaver`.
Use `await` properly; never mix sync/async DB drivers.

---

## Code Style — TypeScript/React (frontend/)

### Formatting

No Prettier configured. Follow existing style:
- 3-space indentation (some files use tabs — be consistent within a file).
- Single quotes for strings.
- Trailing commas in multi-line structures.
- Semicolons at end of statements.

### Imports

Use the `@/` path alias (maps to `./src/*`):

```typescript
import { useChat } from '@/hooks/useChat';
import type { ChatMessage, WSMessage } from '@/types/chat';
import ChatHeader from './ChatHeader';
```

Use `import type` for type-only imports (enforced by `verbatimModuleSyntax`).
Group: external packages first, then `@/` aliased, then relative `./` imports.

### TypeScript Configuration

Strict mode enabled. Key flags: `noUnusedLocals`, `noUnusedParameters`, `verbatimModuleSyntax`, `erasableSyntaxOnly`, `noFallthroughCasesInSwitch`.

### Component Conventions

- Functional components only (React 19).
- One component per file. File name matches component name in PascalCase (e.g., `ChatInput.tsx`).
- Export default for page/container components; named exports for reusable pieces.
- Props interface named `Props` (or component-specific like `ChatInputProps`).
- Custom hooks prefixed with `use` (e.g., `useChat`).

### Styling

- Tailwind CSS 4 utility classes inline. No CSS modules.
- `cn()` helper (tailwind-merge + clsx) for conditional classes.
- shadcn/ui components live in `src/components/ui/`.

### State & Context

- React context for global config (`RamonContext`).
- Local state with `useState`/`useRef` in hooks.
- WebSocket managed via `useRef<WebSocket>` in custom hooks.

### Error Handling

- `try/catch` around `localStorage`, `fetch`, and `JSON.parse`.
- `console.error()` for non-critical client errors.
- Graceful fallbacks (e.g., default avatar when props missing).

---

## Environment Variables

Each sub-project uses `.env` files (gitignored). See `.env.example` for required vars.
Never commit `.env` files or secrets. Key variables: `OPENAI_API_KEY`, `TAVILY_API_KEY`, `APP_KEY`, `DATABASE_URL`.

---

## Git Conventions

- No CI/CD configured. No pre-commit hooks.
- Commit messages: imperative mood, lowercase, concise (< 72 chars).
  Examples: `add product search tool`, `fix websocket disconnect handling`.
- One logical change per commit.
