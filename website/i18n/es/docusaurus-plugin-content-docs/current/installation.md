---
id: installation
sidebar_position: 2
title: Instalación
---

# Instalación

Renfe Tracker puede ejecutarse con [Docker](https://docs.docker.com/get-docker/) (Opciones 1 y 2, recomendado) o de forma nativa con [uv](https://docs.astral.sh/uv/) y Node.js — sin necesidad de Docker (Opción 3).

La forma **recomendada** de ejecutarlo es con Docker Compose, aunque también se admiten `docker run` y la ejecución nativa sin Docker.

---

## Opción 1 — Docker Compose (recomendado) {#docker-compose}

Docker Compose es la opción más sencilla para un despliegue permanente y siempre activo. El archivo compose gestiona los volúmenes, los reinicios automáticos y la configuración de variables de entorno en un solo lugar.

### 1. Obtener el archivo compose

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/JavierMonton/renfe-tracker/main/docker-compose.example.yml
```

### 2. (Opcional) Configurar variables de entorno

Abre `docker-compose.yml` y descomenta / rellena las opciones que necesites:

```yaml
services:
  app:
    image: jmonton/renfe-tracker:latest
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

### 3. Iniciar

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

# Obtener la última imagen y reiniciar
docker compose pull
docker compose up -d
```

Los datos en `./data` nunca se modifican con estos comandos.

---

## Opción 2 — `docker run` {#docker-run}

Usa esta opción si prefieres gestionar el contenedor manualmente o integrarlo en una configuración existente.

### Ejecutar el contenedor

```bash
docker run -d \
  --name renfe-tracker \
  --restart unless-stopped \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  jmonton/renfe-tracker:latest
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
  jmonton/renfe-tracker:latest
```

Para actualizar a una versión más reciente:

```bash
docker pull jmonton/renfe-tracker:latest
docker rm -f renfe-tracker
# vuelve a ejecutar el comando docker run anterior
```

Abre **http://localhost:8000**.

---

## Opción 3 — Sin Docker (UV + Node.js) {#no-docker}

Ejecuta todo de forma nativa, sin necesidad de Docker. Requiere [uv](https://docs.astral.sh/uv/) (gestor de paquetes Python) y Node.js 18+.

### Modo producción

Compila el frontend una vez y ejecuta un único proceso que sirve tanto la API como la interfaz web:

```bash
# Instalar dependencias Python
uv sync

# Compilar el frontend
cd frontend && npm install && npm run build && cd ..

# Iniciar (API + frontend en http://localhost:8000)
uv run uvicorn app.main:app --port 8000
```

Abre **http://localhost:8000**.

### Modo desarrollo

Para colaboradores que quieren recarga en caliente en el frontend y el backend. Requiere dos terminales:

```bash
# Terminal 1 — Backend (recarga automática al cambiar el código)
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2 — Frontend (servidor de desarrollo Vite en http://localhost:5173)
cd frontend
npm install
npm run dev
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
