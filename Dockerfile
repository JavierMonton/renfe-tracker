# Renfe Tracker – FastAPI app (Python 3.11, uv). Playwright/Chromium optional (RENFE_BACKEND=playwright).
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# System deps for Chromium (Playwright), when using RENFE_BACKEND=playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 \
    libnss3 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 \
    xdg-utils wget \
    && rm -rf /var/lib/apt/lists/*

# Install project and dependencies with uv (frozen lockfile)
COPY pyproject.toml uv.lock ./
COPY app/ app/
COPY renfe_mcp/ renfe_mcp/
RUN uv sync --frozen --no-dev

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN uv run playwright install chromium

# Non-root user; Chromium must be readable by appuser
RUN useradd -r -u 1000 appuser \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /ms-playwright 2>/dev/null || true
USER appuser

ENV DATA_DIR=/data
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
