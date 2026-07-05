# RAMon CLI

Command-line tools for testing and interacting with the RAMon chatbot.

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

This installs the `chatbot` package in editable mode.

### 3. Configure environment variables

Create a `.env` file or create a symlink to the root `.env`:

```bash
ln -s ../.env .env
```

Check ../.env.example

## Available Scripts

### demo.py

Runs predefined test scenarios to verify chatbot functionality:

```bash
python demo.py
```

**Test scenarios:**
1. Product recommendation - Asks for camera kit recommendations
2. Technical compatibility - Checks RAM compatibility with a motherboard

### show_graph.py

Generates a visualization of the LangGraph workflow:

```bash
python show_graph.py                    # Saves to ../chatbot/graph.png
python show_graph.py ./my_graph.png     # Saves to custom path
```
