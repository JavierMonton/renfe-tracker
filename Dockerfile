# Renfe Tracker – FastAPI app (Python 3.11, uv). Integrated Renfe library (GTFS + DWR); no browser.
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Install project and dependencies with uv (frozen lockfile)
COPY pyproject.toml uv.lock README.md ./
COPY app/ app/
COPY renfe_mcp/ renfe_mcp/
RUN uv sync --frozen --no-dev

RUN useradd -r -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
ENV HOME=/app
ENV DATA_DIR=/data
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
