# syntax=docker/dockerfile:1
# Renfe Tracker – FastAPI app (Python 3.11, uv) with a React+Tailwind frontend build.

FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm/ \
    npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS base

# Install uv and gosu (entrypoint fixes volume permissions so app can create DB on first run)
RUN --mount=type=cache,target=/root/.cache/pip/ \
    --mount=type=cache,target=/var/lib/apt/ \
    --mount=type=cache,target=/var/cache/apt/ \
  pip install uv \
  && apt-get update && apt-get install -y --no-install-recommends gosu

COPY --chmod=0755 entrypoint.sh /entrypoint.sh
WORKDIR /app

FROM base AS dependencies

# Install project and dependencies with uv (frozen lockfile)
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv/ \
    uv sync --frozen --no-dev

FROM base AS app

COPY app/ app/
COPY renfe_mcp/ renfe_mcp/
# Bundle i18n translation files so the backend can generate localised emails
COPY frontend/src/i18n/ app/i18n/

# Replace static assets with compiled React build
COPY --from=frontend-build /frontend/dist/ app/static/

FROM base AS final

# Default run user is 1000:1000; override at runtime with PUID/PGID. No named user needed (entrypoint uses gosu with numeric id).
COPY --chown=1000:1000 --from=dependencies /app /app
COPY --chown=1000:1000 --from=app /app /app

ENV HOME=/app
ENV DATA_DIR=/data
VOLUME [ "/data" ]
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
