# Medical Record Inspector - Docker Image
# Based on official Python 3.11 slim image for smaller size

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for PDF export if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/
COPY cli/ ./cli/
COPY generators/ ./generators/
COPY templates/ ./templates/
COPY data/ ./data/
COPY docs/ ./docs/

# Copy config example
COPY config.yaml.example .
COPY .env.example .

# Copy startup scripts
COPY start.sh .
RUN chmod +x start.sh

# Copy README and other files
COPY README.md .
COPY README_EN.md .

# Create necessary directories
RUN mkdir -p /app/data/cache /app/data/history /app/logs /app/reports

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0

# Set default command
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
