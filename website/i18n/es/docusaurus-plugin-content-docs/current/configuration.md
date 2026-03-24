---
id: configuration
sidebar_position: 3
title: Configuración
---

# Configuración

Toda la configuración se realiza mediante variables de entorno. Con Docker Compose, establécelas en tu `docker-compose.yml` o en un archivo `.env` en el mismo directorio.

## Variables de entorno

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `DATA_DIR` | `./data` | Directorio donde se almacenan la base de datos SQLite y los datos GTFS. Dentro de Docker es `/data`. |
| `SQLITE_PATH` | `{DATA_DIR}/renfe_tracker.db` | Permite sobreescribir la ruta del archivo de base de datos. |
| `RENFE_GTFS_DIR` | `{DATA_DIR}/renfe_schedule` | Directorio para los datos de horarios GTFS de Renfe (descargados automáticamente). |
| `RENFE_MOCK` | `0` | Establecer a `1` para devolver trenes simulados en lugar de consultar a Renfe. Útil para probar la interfaz. |
| `RENFE_POSSIBLE_TRAINS` | `1` | Establecer a `0` para desactivar la función de trenes posibles. |
| `RENFE_REFERENCE_WEEKS` | `10` | Cuántas semanas de referencia del mismo día de la semana usar para estimar rangos de precios e inferir trenes posibles. Establecer a `0` para desactivar. |
| `RENFE_PRICE_HISTORY_DAYS` | `365` | Cuántos días conservar el historial global de precios. Los registros más antiguos son eliminados por el trabajo de mantenimiento nocturno. |
| `PORT` | `8000` | Puerto del host expuesto por el contenedor. |
| `PUID` | _(no definido)_ | Si se establece, el punto de entrada hará `chown /data` con este ID de usuario. |
| `PGID` | _(no definido)_ | ID de grupo complementario a `PUID`. |

## Correo electrónico (SMTP)

Estas variables configuran la conexión SMTP usada para las alertas por correo. La dirección del destinatario y el asunto se configuran por notificación en la interfaz.

| Variable | Descripción |
|----------|-------------|
| `SMTP_HOST` | Nombre de host del servidor SMTP |
| `SMTP_PORT` | Puerto — `587` (STARTTLS, por defecto), `465` (SSL) o `25` (sin cifrado) |
| `SMTP_USERNAME` | Nombre de usuario SMTP |
| `SMTP_PASSWORD` | Contraseña SMTP |
| `SMTP_USE_STARTTLS` | `true` o `false`. Por defecto `true`. Establecer a `false` para servidores sin cifrado/SSL. |
| `SMTP_FROM` | Dirección del remitente. Por defecto usa `SMTP_USERNAME` si no se establece. |

## Home Assistant

| Variable | Descripción |
|----------|-------------|
| `HA_URL` | URL base de tu instancia de Home Assistant, p. ej. `http://homeassistant.local:8123` |
| `HA_TOKEN` | Token de acceso de larga duración generado en la página de perfil de HA |

## Ejemplo de archivo `.env`

```dotenv
PORT=9000
PUID=1000
PGID=1000

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=youraddress@gmail.com
SMTP_PASSWORD=your-app-password

HA_URL=http://192.168.1.100:8123
HA_TOKEN=eyJhbGciOiJIUz...
```

Luego referencíalo desde `docker-compose.yml`:

```yaml
services:
  app:
    build: .
    env_file: .env
    ports:
      - "${PORT:-8000}:8000"
    volumes:
      - ./data:/data
    restart: unless-stopped
```
