---
id: intro
slug: /
sidebar_position: 1
title: Introducción
---

# Renfe Tracker

**Renfe Tracker** es una aplicación web autoalojada que monitoriza los precios de los trenes de Renfe (Media/Larga Distancia) y te avisa cuando cambian. Se ejecuta completamente dentro de un único contenedor Docker — sin cuentas en la nube, sin suscripciones, sin servicios de terceros.

## Qué hace

- **Busca trenes** entre cualquier estación de Renfe y muestra los precios actuales junto con rangos históricos.
- **Detecta trenes antes de que se pongan a la venta** — la aplicación predice qué trenes es probable que se publiquen basándose en los horarios pasados de cada día de la semana.
- **Sigue viajes** — configura la aplicación para comprobar un tren específico en un horario configurable y registra cada cambio de precio.
- **Recibe alertas** — recibe notificaciones por correo electrónico, Home Assistant o notificaciones del navegador siempre que cambie el precio de un viaje seguido.

## Cómo funciona

El backend es una aplicación Python/FastAPI respaldada por una base de datos SQLite. Utiliza un cliente de Renfe propio (horarios GTFS + extracción de precios en vivo) por lo que no depende de APIs externas ni de un navegador ejecutándose en tu máquina.

El frontend es una aplicación de página única React 19 + TypeScript servida por el mismo proceso. Todo persiste en un único volumen montado (`/data`), lo que hace que las copias de seguridad sean triviales.

```
┌─────────────────────────────────────┐
│          Contenedor Docker           │
│                                     │
│  FastAPI  ──────►  SQLite (/data)   │
│    │                                │
│  APScheduler (comprobaciones)       │
│    │                                │
│  Cliente Renfe (GTFS + DWR)         │
│                                     │
│  React SPA (archivos estáticos)     │
└─────────────────────────────────────┘
```

## Inicio rápido

```bash
# 1. Clona el repositorio
git clone https://github.com/JavierMonton/renfe-tracker.git
cd renfe-tracker

# 2. Copia el archivo compose de ejemplo
cp docker-compose.example.yml docker-compose.yml

# 3. Inicia la aplicación
docker compose up --build -d

# 4. Abre http://localhost:8000
```

Consulta la página de [Instalación](./installation) para más detalles, incluidas las opciones de `docker run` y desarrollo local.

## Funcionalidades

### Rangos de precio y trenes posibles

Al buscar trenes, la app muestra rangos de precio estimados basados en datos históricos y destaca los trenes que pueden no estar publicados aún para tu fecha.

![Captura de búsqueda](/img/search-screenshot.png)

### Sigue múltiples viajes

Sigue varios viajes a la vez y recibe notificaciones cuando cambie el precio.

![Captura de viajes](/img/trips-screenshot.png)

### Historial de cambios de precio

Consulta el historial completo de cambios de precio de cualquier viaje seguido.

![Captura de historial de precios](/img/prices-screenshot.png)
