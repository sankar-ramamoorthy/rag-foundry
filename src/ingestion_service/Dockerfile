# Use a Python 3.12 slim image with uv preinstalled
FROM astral/uv:python3.12-bookworm-slim

# Set working directory inside container
WORKDIR /app

# Copy entire repo (so pyproject.toml is available)
COPY . .

# Install all dependencies from pyproject.toml
RUN uv sync

# Expose FastAPI port
EXPOSE 8001

# Run FastAPI app
CMD ["uv", "run", "uvicorn", "src.ingestion_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
