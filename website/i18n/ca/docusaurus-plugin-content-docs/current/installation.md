---
id: installation
sidebar_position: 2
title: Instal·lació
---

# Instal·lació

Renfe Tracker es distribueix com a imatge Docker. La manera **recomanada** d'executar-lo és amb Docker Compose, tot i que `docker run` i el desenvolupament local sense Docker també estan admesos.

---

## Opció 1 — Docker Compose (recomanat) {#docker-compose}

Docker Compose és l'opció més senzilla per a un desplegament permanent i sempre actiu. El fitxer compose gestiona els volums, els reinicis automàtics i la configuració de variables d'entorn en un sol lloc.

### 1. Obtenir els fitxers

```bash
git clone https://github.com/JavierMonton/renfe-tracker.git
cd renfe-tracker
cp docker-compose.example.yml docker-compose.yml
```

### 2. (Opcional) Configurar variables d'entorn

Obre `docker-compose.yml` i descomenta / omple les opcions que necessitis:

```yaml
services:
  app:
    build: .
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

### 3. Construir i iniciar

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

# Obtenir el darrer codi i reconstruir
docker compose pull
docker compose up -d
```

Les dades a `./data` mai es modifiquen amb aquestes ordres.

---

## Opció 2 — `docker run` {#docker-run}

Usa aquesta opció si prefereixes gestionar el contenidor manualment o integrar-lo en una configuració existent.

### Construir la imatge

```bash
git clone https://github.com/JavierMonton/renfe-tracker.git
cd renfe-tracker
docker build -t renfe-tracker .
```

### Executar el contenidor

```bash
docker run -d \
  --name renfe-tracker \
  --restart unless-stopped \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  renfe-tracker
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
  renfe-tracker
```

Obre **http://localhost:8000**.

---

## Opció 3 — Desenvolupament local (sense Docker) {#local-dev}

Útil si vols modificar el codi. Requereix [uv](https://github.com/astral-sh/uv) (gestor de paquets Python) i Node.js 18+.

### Backend

```bash
# Instal·lar dependències
uv sync

# Iniciar el servidor API (recàrrega automàtica en canviar el codi)
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

En un segon terminal:

```bash
cd frontend
npm install
npm run dev      # Servidor de desenvolupament Vite a http://localhost:5173
                 # Totes les peticions /api es redirigeixen a :8000
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
