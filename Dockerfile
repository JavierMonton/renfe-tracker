# Renfe Tracker – FastAPI app (Python 3.11, uv). Integrated Renfe library (GTFS + DWR); no browser.
FROM python:3.11-slim

WORKDIR /app

# Install uv and gosu (entrypoint fixes volume permissions so app can create DB on first run)
RUN pip install --no-cache-dir uv \
  && apt-get update && apt-get install -y --no-install-recommends gosu \
  && rm -rf /var/lib/apt/lists/*

# Install project and dependencies with uv (frozen lockfile)
COPY pyproject.toml uv.lock README.md ./
COPY app/ app/
COPY renfe_mcp/ renfe_mcp/
RUN uv sync --frozen --no-dev

# Default run user is 1000:1000; override at runtime with PUID/PGID. No named user needed (entrypoint uses gosu with numeric id).
RUN chown -R 1000:1000 /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV HOME=/app
ENV DATA_DIR=/data
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
