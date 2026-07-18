# Development Dockerfile for RAMon Backend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg, pgvector, and cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy chatbot package first (it's a local dependency)
COPY chatbot /app/chatbot

# Copy backend code and install requirements
COPY backend/ /app/backend/
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# Set up crontab for the sync worker
COPY backend/crontab /etc/cron.d/ramon-sync
RUN chmod 0644 /etc/cron.d/ramon-sync && crontab /etc/cron.d/ramon-sync

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose the FastAPI port
EXPOSE 8000

# Default command: run entrypoint which starts cron + uvicorn
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
