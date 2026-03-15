# Renfe Tracker – FastAPI app (Python 3.11, Playwright/Chromium para sesión Renfe)
FROM python:3.11-slim

WORKDIR /app

# Dependencias de sistema para Chromium (Playwright)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 \
    libnss3 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 \
    xdg-utils wget \
    && rm -rf /var/lib/apt/lists/*

# Python y Playwright; instalar Chromium en ruta fija para el usuario de la app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install chromium

# Código de la aplicación
COPY app/ app/

# Usuario no root; Chromium debe ser legible por appuser
RUN useradd -r -u 1000 appuser \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /ms-playwright
USER appuser

# App writes DB to /data (mounted from host in compose)
ENV DATA_DIR=/data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
