---
id: trip-tracking
sidebar_position: 3
title: Seguimiento de Viajes
---

# Seguimiento de Viajes

El seguimiento de viajes es la función principal de Renfe Tracker. Una vez que encuentras un tren que te interesa, puedes **seguirlo** — la aplicación comprobará el precio periódicamente y registrará cada cambio, para que siempre sepas cuándo comprar.

## Añadir un viaje seguido

1. Ve a la página de **Búsqueda** e introduce tu origen, destino y fecha de viaje.
2. Encuentra el tren que quieres en los resultados.
3. Haz clic en **Seguir** para abrir el diálogo de seguimiento.
4. Elige un **intervalo de comprobación** (con qué frecuencia debe la aplicación comprobar el precio).
5. Confirma — el viaje ya está siendo seguido.

Puedes seguir la misma ruta con diferentes trenes, o el mismo tren en múltiples fechas, como viajes seguidos separados.

## Cómo funciona la comprobación de precios

La aplicación ejecuta un trabajo del planificador **cada minuto**. Para cada viaje seguido que deba ser comprobado (según su intervalo configurado):

1. Consulta a Renfe el precio actual de ese tren específico.
2. Redondea el precio a 2 decimales (usando ROUND_HALF_UP).
3. Compara con el último precio registrado.
4. Si el precio ha cambiado:
   - Registra un **evento de precio** (marca de tiempo + nuevo precio).
   - Actualiza la dirección del cambio de precio (`subida` / `bajada`).
   - Envía las [notificaciones](./notifications) configuradas.
5. Siempre actualiza `last_checked_at` y registra el precio en las muestras históricas.

## Ver el historial de precios

Haz clic en cualquier viaje seguido en la página de inicio para abrir su **página de detalle**. Verás una línea de tiempo cronológica de cada cambio de precio detectado, con flechas que indican si el precio subió o bajó y en cuánto.

## Intervalo de comprobación

El intervalo de comprobación es configurable por viaje. Los intervalos más cortos significan una detección más rápida pero más consultas a Renfe. Considera:

- **5–15 minutos** para viajes donde esperas cambios de precio rápidos (p. ej. cerca de la fecha de viaje).
- **1–4 horas** para viajes lejanos en el futuro donde las fluctuaciones diarias son más comunes.

## Gestionar viajes seguidos

Desde la página de inicio puedes:

- **Ver** el historial de precios de cualquier viaje seguido.
- **Eliminar** un viaje que ya no quieres seguir.

Los viajes están agrupados por ruta en la página de inicio para facilitar la visualización.

:::info
Los trenes posibles (aún no publicados por Renfe) también se pueden seguir. El comprobador de precios simplemente no encontrará precio hasta que Renfe publique el tren, momento en el que el primer precio se registra como valor inicial y el seguimiento comienza normalmente.
:::
