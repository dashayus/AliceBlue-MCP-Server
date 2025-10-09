FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app/src

# Run using mcp command
CMD ["python", "-m", "mcp", "run", "aliceblue_server.server:create_server"]
