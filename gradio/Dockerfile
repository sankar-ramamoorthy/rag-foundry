FROM astral/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy only what this container needs: project metadata + src tree
COPY pyproject.toml ./
COPY src ./src

# Install only the UI extras for this image
RUN uv sync --extra ui --no-dev

ENV API_BASE_URL=http://ingestion_service:8001
ENV PYTHONPATH=/app/src

# Run the Gradio UI module from the src layout
CMD ["uv", "run", "-m", "ingestion_service.ui.gradio_app"]
