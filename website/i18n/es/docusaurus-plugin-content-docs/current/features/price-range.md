---
id: price-range
sidebar_position: 2
title: Rango de Precios
---

# Rango de Precios

Para cada tren mostrado en los resultados de búsqueda y en tu lista de viajes seguidos, Renfe Tracker muestra no solo el **precio actual**, sino también un **rango histórico de precios** — los precios mínimo y máximo observados para ese tren en la misma ruta y día de la semana.

## ¿Por qué es útil?

Los precios de los trenes de Renfe fluctúan. Saber que un billete cuesta actualmente €45 es más útil cuando también sabes que ha oscilado entre €32 y €67 en los últimos meses. Puedes juzgar si ahora es un buen momento para comprar o si deberías esperar y seguir el precio.

## Cómo se recopilan los precios

La aplicación construye su conocimiento de precios a partir de dos fuentes:

### 1. Búsquedas de semanas de referencia (en el momento de la búsqueda)

Cuando buscas un tren, la aplicación también obtiene los precios para el **mismo tren en el mismo día de la semana en múltiples semanas anteriores** (controlado por `RENFE_REFERENCE_WEEKS`, por defecto 10). Todos los precios encontrados — tanto para la fecha solicitada como para las fechas de referencia — se almacenan en:

- **`price_samples`** — precios únicos observados por viaje seguido (usado para el rango por viaje).
- **`price_history`** — precios globales indexados por `(origen, destino, día_semana, tren, hora_salida)` (usado en todas las búsquedas para esa ruta).

### 2. Comprobaciones periódicas del planificador

Cada vez que el comprobador de precios se ejecuta para un viaje seguido, el precio que encuentra también se registra en ambas tablas. Con el tiempo, esto construye una imagen más rica de cómo evolucionan los precios en una ruta dada.

## Dónde se muestra

**Página de resultados de búsqueda** — cada tarjeta de tren muestra el precio actual más un rango estimado:

```
AVE · 07:00 → 09:30
€ 45.10   Rango: €32.00 – €67.50
```

**Lista de viajes seguidos** — el mismo rango se muestra junto al último precio conocido de cada viaje seguido, para que siempre tengas contexto cuando llegue una notificación de cambio de precio.

## Retención de datos

El historial global de precios se conserva durante `RENFE_PRICE_HISTORY_DAYS` días (por defecto 365). Un trabajo de mantenimiento nocturno elimina los registros más antiguos que ese umbral para que la base de datos no crezca sin límite.

| Variable | Valor por defecto | Efecto |
|----------|-------------------|--------|
| `RENFE_REFERENCE_WEEKS` | `10` | Semanas de datos históricos obtenidos en el momento de la búsqueda |
| `RENFE_PRICE_HISTORY_DAYS` | `365` | Tiempo que se conservan los registros globales de precios |

:::note
Los rangos de precios son estimaciones basadas en datos observados. Reflejan los precios vistos por el rastreador en fechas de referencia, no el historial completo de todos los precios que Renfe haya ofrecido.
:::
