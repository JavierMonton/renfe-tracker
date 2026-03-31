---
id: installation
sidebar_position: 2
title: Instal·lació
---

# Instal·lació

Renfe Tracker pot executar-se amb [Docker](https://docs.docker.com/get-docker/) (Opcions 1 i 2, recomanat) o de manera nativa amb [uv](https://docs.astral.sh/uv/) i Node.js — sense necessitat de Docker (Opció 3).

La manera **recomanada** d'executar-lo és amb Docker Compose, tot i que `docker run` i l'execució nativa sense Docker també estan admesos.

---

## Opció 1 — Docker Compose (recomanat) {#docker-compose}

Docker Compose és l'opció més senzilla per a un desplegament permanent i sempre actiu. El fitxer compose gestiona els volums, els reinicis automàtics i la configuració de variables d'entorn en un sol lloc.

### 1. Obtenir el fitxer compose

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/JavierMonton/renfe-tracker/main/docker-compose.example.yml
```

### 2. (Opcional) Configurar variables d'entorn

Obre `docker-compose.yml` i descomenta / omple les opcions que necessitis:

```yaml
services:
  app:
    image: jmonton/renfe-tracker:latest
    ports:
      - "${PORT:-8000}:8000"
    environment:
      DATA_DIR: /data

      # ── Alertes per correu ────────────────────────────────
      # SMTP_HOST: smtp.example.com
      # SMTP_PORT: 587
      # SMTP_USERNAME: alerts@example.com
      # SMTP_PASSWORD: your-smtp-password

      # ── Alertes de Home Assistant ────────────────────────
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

Obre **http://localhost:8000**. Per usar un port diferent, estableix `PORT` en un fitxer `.env` o directament:

```bash
PORT=9000 docker compose up -d
```

### 4. Aturar / actualitzar

```bash
# Aturar
docker compose down

# Obtenir la darrera imatge i reiniciar
docker compose pull
docker compose up -d
```

Les dades a `./data` mai es modifiquen amb aquestes ordres.

---

## Opció 2 — `docker run` {#docker-run}

Usa aquesta opció si prefereixes gestionar el contenidor manualment o integrar-lo en una configuració existent.

### Executar el contenidor

```bash
docker run -d \
  --name renfe-tracker \
  --restart unless-stopped \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  jmonton/renfe-tracker:latest
```

Amb variables d'entorn per a correu electrònic i Home Assistant:

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

Per actualitzar a una versió més recent:

```bash
docker pull jmonton/renfe-tracker:latest
docker rm -f renfe-tracker
# torna a executar l'ordre docker run anterior
```

Obre **http://localhost:8000**.

---

## Opció 3 — Sense Docker (UV + Node.js) {#no-docker}

Executa-ho tot de manera nativa, sense necessitat de Docker. Requereix [uv](https://docs.astral.sh/uv/) (gestor de paquets Python) i Node.js 18+.

### Mode producció

Compila el frontend una vegada i executa un únic procés que serveix tant l'API com la interfície web:

```bash
# Instal·lar dependències Python
uv sync

# Compilar el frontend
cd frontend && npm install && npm run build && cd ..

# Iniciar (API + frontend a http://localhost:8000)
uv run uvicorn app.main:app --port 8000
```

Obre **http://localhost:8000**.

### Mode desenvolupament

Per a col·laboradors que volen recàrrega en calent al frontend i al backend. Requereix dos terminals:

```bash
# Terminal 1 — Backend (recàrrega automàtica en canviar el codi)
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2 — Frontend (servidor de desenvolupament Vite a http://localhost:5173)
cd frontend
npm install
npm run dev
```

El servidor de desenvolupament Vite redirigeix les crides `/api` al backend FastAPI, de manera que obtens recàrrega en calent al frontend mentre el backend gestiona les dades.

### Executar les proves

```bash
uv run pytest          # totes les proves (Renfe es simula, sense crides de xarxa reals)
uv run pytest -v       # sortida detallada
```

---

## Persistència de dades

Totes les dades de l'aplicació viuen al directori `./data` (o allà on apunti el volum):

| Ruta | Contingut |
|------|-----------|
| `./data/renfe_tracker.db` | Base de dades SQLite (viatges, preus, notificacions) |
| `./data/renfe_schedule/` | Dades GTFS de Renfe (descarregades automàticament a la primera cerca) |

La base de dades i els fitxers GTFS sobreviuen als reinicis, reconstruccions i actualitzacions del contenidor. Fes una còpia de seguretat del directori `./data` per conservar els teus viatges seguits i l'historial de preus.

### Propietat dels fitxers

El contenidor s'executa com a root per defecte per poder crear i escriure la base de dades al primer inici. Si vols que els fitxers de l'amfitrió siguin del teu usuari, estableix `PUID` i `PGID`:

```yaml
environment:
  PUID: 1000
  PGID: 1000
```

O després del primer inici:

```bash
chown -R $(id -u):$(id -g) ./data
```
