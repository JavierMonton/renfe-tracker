---
id: intro
slug: /
sidebar_position: 1
title: Introducció
---

# Renfe Tracker

**Renfe Tracker** és una aplicació web auto-allotjada que monitora els preus dels trens de Renfe (Media/Larga Distancia) i t'avisa quan canvien. S'executa completament dins d'un únic contenidor Docker — sense comptes al núvol, sense subscripcions, sense serveis de tercers.

## Què fa

- **Cerca trens** entre qualsevol estació de Renfe i mostra els preus actuals juntament amb rangs històrics.
- **Detecta trens abans que surtin a la venda** — l'aplicació prediu quins trens és probable que es publiquin basant-se en els horaris passats de cada dia de la setmana.
- **Segueix viatges** — configura l'aplicació per comprovar un tren específic amb un horari configurable i registra cada canvi de preu.
- **Rep alertes** — rep notificacions per correu electrònic, Home Assistant o notificacions del navegador sempre que canviï el preu d'un viatge seguit.

## Com funciona

El backend és una aplicació Python/FastAPI recolzada per una base de dades SQLite. Utilitza un client de Renfe propi (horaris GTFS + extracció de preus en viu) de manera que no depèn d'APIs externes ni d'un navegador executant-se a la teva màquina.

El frontend és una aplicació de pàgina única React 19 + TypeScript servida pel mateix procés. Tot persisteix en un únic volum muntat (`/data`), la qual cosa fa que les còpies de seguretat siguin trivials.

```
┌─────────────────────────────────────┐
│          Contenidor Docker           │
│                                     │
│  FastAPI  ──────►  SQLite (/data)   │
│    │                                │
│  APScheduler (comprovacions)        │
│    │                                │
│  Client Renfe (GTFS + DWR)          │
│                                     │
│  React SPA (fitxers estàtics)       │
└─────────────────────────────────────┘
```

## Inici ràpid

Necessites tenir [Docker](https://docs.docker.com/get-docker/) instal·lat a la teva màquina.

```bash
# 1. Descarrega el fitxer compose
curl -o docker-compose.yml https://raw.githubusercontent.com/JavierMonton/renfe-tracker/main/docker-compose.example.yml

# 2. Inicia l'aplicació (la imatge es descarrega automàticament de Docker Hub)
docker compose up -d

# 3. Obre http://localhost:8000
```

Consulta la pàgina d'[Instal·lació](./installation) per a més detalls, incloent-hi les opcions de `docker run` i desenvolupament local.

## Funcionalitats

### Rangs de preu i trens possibles

En cercar trens, l'app mostra rangs de preu estimats basats en dades històriques i destaca els trens que poden no estar publicats encara per a la teva data.

![Captura de cerca](/img/search-screenshot.png)

### Segueix múltiples viatges

Segueix diversos viatges alhora i rep notificacions quan canviï el preu.

![Captura de viatges](/img/trips-screenshot.png)

### Historial de canvis de preu

Consulta l'historial complet de canvis de preu de qualsevol viatge seguit.

![Captura d'historial de preus](/img/prices-screenshot.png)
