---
id: price-range
sidebar_position: 2
title: Rang de Preus
---

# Rang de Preus

Per a cada tren mostrat als resultats de cerca i a la llista de viatges seguits, Renfe Tracker mostra no només el **preu actual**, sinó també un **rang històric de preus** — els preus mínim i màxim observats per a aquell tren en la mateixa ruta i dia de la setmana.

## Per què és útil?

Els preus dels trens de Renfe fluctuen. Saber que un bitllet costa actualment €45 és més útil quan també saps que ha oscil·lat entre €32 i €67 en els darrers mesos. Pots jutjar si ara és un bon moment per comprar o si hauries d'esperar i seguir el preu.

## Com es recopilen els preus

L'aplicació construeix el seu coneixement de preus a partir de dues fonts:

### 1. Cerques de setmanes de referència (en el moment de la cerca)

Quan cerques un tren, l'aplicació també obté els preus per al **mateix tren en el mateix dia de la setmana en múltiples setmanes anteriors** (controlat per `RENFE_REFERENCE_WEEKS`, per defecte 10). Tots els preus trobats — tant per a la data sol·licitada com per a les dates de referència — s'emmagatzemen a:

- **`price_samples`** — preus únics observats per viatge seguit (usat per al rang per viatge).
- **`price_history`** — preus globals indexats per `(origen, destinació, dia_setmana, tren, hora_sortida)` (usat en totes les cerques per a aquella ruta).

### 2. Comprovacions periòdiques del planificador

Cada vegada que el comprovador de preus s'executa per a un viatge seguit, el preu que troba també es registra a les dues taules. Amb el temps, això construeix una imatge més rica de com evolucionen els preus en una ruta donada.

## On es mostra

**Pàgina de resultats de cerca** — cada targeta de tren mostra el preu actual més un rang estimat:

```
AVE · 07:00 → 09:30
€ 45.10   Rang: €32.00 – €67.50
```

**Llista de viatges seguits** — el mateix rang es mostra al costat del darrer preu conegut de cada viatge seguit, perquè sempre tinguis context quan arribi una notificació de canvi de preu.

## Retenció de dades

L'historial global de preus es conserva durant `RENFE_PRICE_HISTORY_DAYS` dies (per defecte 365). Un treball de manteniment nocturn elimina els registres més antics que aquest llindar perquè la base de dades no creixi sense límit.

| Variable | Valor per defecte | Efecte |
|----------|-------------------|--------|
| `RENFE_REFERENCE_WEEKS` | `10` | Setmanes de dades històriques obtingudes en el moment de la cerca |
| `RENFE_PRICE_HISTORY_DAYS` | `365` | Temps que es conserven els registres globals de preus |

:::note
Els rangs de preus són estimacions basades en dades observades. Reflecteixen els preus vistos pel rastrejador en dates de referència, no l'historial complet de tots els preus que Renfe hagi ofert mai.
:::
