---
id: installation
sidebar_position: 2
title: Instalación
---

# Instalación

Renfe Tracker se distribuye como imagen Docker. La forma **recomendada** de ejecutarlo es con Docker Compose, aunque también se admiten `docker run` y el desarrollo local sin Docker.

---

## Opción 1 — Docker Compose (recomendado) {#docker-compose}

Docker Compose es la opción más sencilla para un despliegue permanente y siempre activo. El archivo compose gestiona los volúmenes, los reinicios automáticos y la configuración de variables de entorno en un solo lugar.

### 1. Obtener los archivos

```bash
git clone https://github.com/JavierMonton/renfe-tracker.git
cd renfe-tracker
cp docker-compose.example.yml docker-compose.yml
```

### 2. (Opcional) Configurar variables de entorno

Abre `docker-compose.yml` y descomenta / rellena las opciones que necesites:

```yaml
services:
  app:
    build: .
    ports:
      - "${PORT:-8000}:8000"
    environment:
      DATA_DIR: /data

      # ── Alertas por correo ────────────────────────────────
      # SMTP_HOST: smtp.example.com
      # SMTP_PORT: 587
      # SMTP_USERNAME: alerts@example.com
      # SMTP_PASSWORD: your-smtp-password

      # ── Alertas de Home Assistant ────────────────────────
      # HA_URL: http://homeassistant.local:8123
      # HA_TOKEN: your-long-lived-access-token

    volumes:
      - ./data:/data
    restart: unless-stopped
```

### 3. Construir e iniciar

```bash
docker compose up -d
```

Abre **http://localhost:8000**. Para usar un puerto diferente, establece `PORT` en un archivo `.env` o de forma directa:

```bash
PORT=9000 docker compose up -d
```

### 4. Detener / actualizar

```bash
# Detener
docker compose down

# Obtener el último código y reconstruir
docker compose pull
docker compose up -d
```

Los datos en `./data` nunca se modifican con estos comandos.

---

## Opción 2 — `docker run` {#docker-run}

Usa esta opción si prefieres gestionar el contenedor manualmente o integrarlo en una configuración existente.

### Construir la imagen

```bash
git clone https://github.com/JavierMonton/renfe-tracker.git
cd renfe-tracker
docker build -t renfe-tracker .
```

### Ejecutar el contenedor

```bash
docker run -d \
  --name renfe-tracker \
  --restart unless-stopped \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  renfe-tracker
```

Con variables de entorno para correo electrónico y Home Assistant:

```bash
docker run -d \
  --name renfe-tracker \
  --restart unless-stopped \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  -e SMTP_HOST=smtp.example.com \
  -e SMTP_PORT=587 \
  -e SMTP_USERNAME=alerts@example.com \
  -e SMTP_PASSWORD=your-password \
  -e HA_URL=http://homeassistant.local:8123 \
  -e HA_TOKEN=your-ha-token \
  renfe-tracker
```

Abre **http://localhost:8000**.

---

## Opción 3 — Desarrollo local (sin Docker) {#local-dev}

Útil si quieres modificar el código. Requiere [uv](https://github.com/astral-sh/uv) (gestor de paquetes Python) y Node.js 18+.

### Backend

```bash
# Instalar dependencias
uv sync

# Iniciar el servidor API (recarga automática al cambiar el código)
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

En una segunda terminal:

```bash
cd frontend
npm install
npm run dev      # Servidor de desarrollo Vite en http://localhost:5173
                 # Todas las peticiones /api se redirigen a :8000
```

El servidor de desarrollo Vite redirige las llamadas `/api` al backend FastAPI, por lo que obtienes recarga en caliente en el frontend mientras el backend gestiona los datos.

### Ejecutar las pruebas

```bash
uv run pytest          # todas las pruebas (Renfe se simula, sin llamadas de red reales)
uv run pytest -v       # salida detallada
```

---

## Persistencia de datos

Todos los datos de la aplicación se almacenan en el directorio `./data` (o donde apunte el volumen):

| Ruta | Contenido |
|------|-----------|
| `./data/renfe_tracker.db` | Base de datos SQLite (viajes, precios, notificaciones) |
| `./data/renfe_schedule/` | Datos GTFS de Renfe (descargados automáticamente en la primera búsqueda) |

La base de datos y los archivos GTFS sobreviven a los reinicios, reconstrucciones y actualizaciones del contenedor. Haz una copia de seguridad del directorio `./data` para conservar tus viajes seguidos e historial de precios.

### Propiedad de archivos

El contenedor se ejecuta como root por defecto para poder crear y escribir la base de datos al primer inicio. Si quieres que los archivos del host sean de tu usuario, establece `PUID` y `PGID`:

```yaml
environment:
  PUID: 1000
  PGID: 1000
```

O después del primer inicio:

```bash
chown -R $(id -u):$(id -g) ./data
```
