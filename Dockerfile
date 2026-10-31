# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source tree
COPY alerts/ ./alerts/
COPY collector/ ./collector/
COPY config/ ./config/
COPY data/ ./data/
COPY detection/ ./detection/
COPY models/ ./models/
COPY simulator/ ./simulator/
COPY storage/ ./storage/
COPY run_live_stream.py .
COPY run_pipeline_demo.py .
COPY .env.example .env

# Create persistent storage directory for offline SQLite buffer
RUN mkdir -p /app/data/cache

# Expose healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', 1883))" || exit 0

# Default command: continuous live telemetry stream and real-time detection
CMD ["python", "run_live_stream.py"]
