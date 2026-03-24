---
id: configuration
sidebar_position: 3
title: Configuració
---

# Configuració

Tota la configuració es fa mitjançant variables d'entorn. Amb Docker Compose, estableix-les al teu `docker-compose.yml` o en un fitxer `.env` al mateix directori.

## Variables d'entorn

| Variable | Valor per defecte | Descripció |
|----------|-------------------|------------|
| `DATA_DIR` | `./data` | Directori on s'emmagatzemen la base de dades SQLite i les dades GTFS. Dins de Docker és `/data`. |
| `SQLITE_PATH` | `{DATA_DIR}/renfe_tracker.db` | Permet sobreescriure la ruta del fitxer de base de dades. |
| `RENFE_GTFS_DIR` | `{DATA_DIR}/renfe_schedule` | Directori per a les dades d'horaris GTFS de Renfe (descarregades automàticament). |
| `RENFE_MOCK` | `0` | Establir a `1` per retornar trens simulats en lloc de consultar Renfe. Útil per provar la interfície. |
| `RENFE_POSSIBLE_TRAINS` | `1` | Establir a `0` per desactivar la funció de trens possibles. |
| `RENFE_REFERENCE_WEEKS` | `10` | Quantes setmanes de referència del mateix dia de la setmana usar per estimar rangs de preus i inferir trens possibles. Establir a `0` per desactivar. |
| `RENFE_PRICE_HISTORY_DAYS` | `365` | Quants dies conservar l'historial global de preus. Els registres més antics s'eliminen pel treball de manteniment nocturn. |
| `PORT` | `8000` | Port de l'amfitrió exposat pel contenidor. |
| `PUID` | _(no definit)_ | Si s'estableix, el punt d'entrada farà `chown /data` amb aquest ID d'usuari. |
| `PGID` | _(no definit)_ | ID de grup complementari a `PUID`. |

## Correu electrònic (SMTP)

Aquestes variables configuren la connexió SMTP usada per a les alertes per correu. L'adreça del destinatari i l'assumpte es configuren per notificació a la interfície.

| Variable | Descripció |
|----------|------------|
| `SMTP_HOST` | Nom d'amfitrió del servidor SMTP |
| `SMTP_PORT` | Port — `587` (STARTTLS, per defecte), `465` (SSL) o `25` (sense xifratge) |
| `SMTP_USERNAME` | Nom d'usuari SMTP |
| `SMTP_PASSWORD` | Contrasenya SMTP |
| `SMTP_USE_STARTTLS` | `true` o `false`. Per defecte `true`. Establir a `false` per a servidors sense xifratge/SSL. |
| `SMTP_FROM` | Adreça del remitent. Per defecte usa `SMTP_USERNAME` si no s'estableix. |

## Home Assistant

| Variable | Descripció |
|----------|------------|
| `HA_URL` | URL base de la teva instància de Home Assistant, p. ex. `http://homeassistant.local:8123` |
| `HA_TOKEN` | Token d'accés de llarga durada generat a la pàgina de perfil de HA |

## Exemple de fitxer `.env`

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

Després referencia'l des de `docker-compose.yml`:

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
