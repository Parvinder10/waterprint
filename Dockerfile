FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and data
COPY config/ ./config/
COPY src/ ./src/
COPY data/ ./data/
COPY reports/ ./reports/

# Set environment
ENV PORT=8088
ENV PYTHONUNBUFFERED=1

EXPOSE 8088

CMD ["sh", "-c", "python -m uvicorn src.api.server:app --host 0.0.0.0 --port ${PORT}"]
