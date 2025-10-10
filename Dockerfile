FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies including Ant-A3 SDK
RUN pip install --no-cache-dir .

# Copy the application code
COPY server.py ./

# Create a non-root user
RUN useradd --create-home --shell /bin/bash mcp
USER mcp

# Expose the port
EXPOSE 8000

# Run the server
CMD ["python", "server.py"]