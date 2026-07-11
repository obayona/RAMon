# Development Dockerfile for RAMon Backend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg and pgvector
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy chatbot package first (it's a local dependency)
COPY chatbot /app/chatbot
RUN pip install --no-cache-dir -e /app/chatbot

# Copy and install backend requirements
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend source code
COPY backend /app/backend

# Make entrypoint executable
RUN chmod +x /app/backend/entrypoint.sh

WORKDIR /app/backend

# Expose the FastAPI port
EXPOSE 8000

# Default command: run uvicorn with reload for development
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
