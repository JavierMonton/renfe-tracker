# Renfe Tracker – FastAPI app (Python 3.11 slim, non-root user, port 8000)
FROM python:3.11-slim

WORKDIR /app

# Install dependencies (no cache to keep image smaller)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app/ app/

# Non-root user (UID 1000; if ./data has permission issues, chown 1000:1000 on host)
RUN useradd -r -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# App writes DB to /data (mounted from host in compose)
ENV DATA_DIR=/data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
