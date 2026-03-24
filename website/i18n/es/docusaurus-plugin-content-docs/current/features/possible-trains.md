---
id: possible-trains
sidebar_position: 1
title: Trenes Posibles
---

# Trenes Posibles

Cuando buscas trenes en una fecha concreta, Renfe Tracker no solo muestra los trenes que Renfe ha publicado actualmente para ese día — también muestra **trenes que aún no se han publicado pero es muy probable que circulen**.

## ¿Por qué es importante?

Renfe publica los horarios de trenes de forma progresiva. Un tren que sabes que circula todos los martes puede que aún no aparezca en los resultados de búsqueda para una fecha que está a muchas semanas vista. Sin esta función, tendrías que seguir comprobando hasta que el tren aparezca antes de poder empezar a seguir su precio.

## Cómo funciona

Cuando buscas trenes en una fecha, la aplicación también obtiene los horarios de trenes para el **mismo día de la semana en múltiples semanas anteriores** (hasta `RENFE_REFERENCE_WEEKS` semanas atrás, por defecto 10). Cualquier tren que:

1. Circuló ese día de la semana en al menos una semana de referencia, **y**
2. **Aún no está publicado** para la fecha solicitada

…se marca como **tren posible**.

```
Fecha solicitada: martes, 15 de abril
Fechas de referencia: martes 8 abr, mar 1 abr, mar 25 mar, …

Trenes en fechas de referencia  ──►  Unión de todos los trenes vistos
                                              │
                                              ▼
                                    Trenes que faltan el 15 abr
                                              │
                                              ▼
                                    Marcados como "trenes posibles"
```

## En la interfaz

Los trenes posibles aparecen en los resultados de búsqueda con un **borde discontinuo** y una insignia **"Tren posible"** para distinguirlos de los trenes publicados confirmados. Su precio se muestra como "no disponible aún" ya que Renfe no lo ha publicado, pero puedes empezar a seguir el viaje de inmediato — el rastreador empezará a comprobar en cuanto Renfe publique un precio.

## Configuración

| Variable | Valor por defecto | Efecto |
|----------|-------------------|--------|
| `RENFE_POSSIBLE_TRAINS` | `1` | Establecer a `0` para desactivar la inferencia de trenes posibles por completo. |
| `RENFE_REFERENCE_WEEKS` | `10` | Número de semanas del mismo día de la semana hacia atrás. Más semanas = mejor cobertura pero primera búsqueda más lenta. |

:::tip
Establece `RENFE_REFERENCE_WEEKS=0` si solo quieres ver los trenes publicados actualmente y omitir las búsquedas históricas. Esto hace las búsquedas más rápidas pero desactiva tanto los trenes posibles como la estimación del rango de precios.
:::
