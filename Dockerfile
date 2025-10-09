FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy the application code
COPY server.py ./
COPY .env ./

# Create a non-root user
RUN useradd --create-home --shell /bin/bash mcp
USER mcp

# Expose the port (if needed, though MCP typically uses stdio)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

# Run the server
CMD ["python", "server.py"]