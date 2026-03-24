---
id: possible-trains
sidebar_position: 1
title: Trens Possibles
---

# Trens Possibles

Quan cerques trens en una data concreta, Renfe Tracker no només mostra els trens que Renfe ha publicat actualment per a aquell dia — també mostra **trens que encara no s'han publicat però és molt probable que circulin**.

## Per què és important?

Renfe publica els horaris de trens de forma progressiva. Un tren que saps que circula cada dimarts pot ser que encara no aparegui als resultats de cerca per a una data que és a moltes setmanes vista. Sense aquesta funció, hauries de continuar comprovant fins que el tren aparegués per poder començar a seguir el seu preu.

## Com funciona

Quan cerques trens en una data, l'aplicació també obté els horaris de trens per al **mateix dia de la setmana en múltiples setmanes anteriors** (fins a `RENFE_REFERENCE_WEEKS` setmanes enrere, per defecte 10). Qualsevol tren que:

1. Va circular aquell dia de la setmana almenys en una setmana de referència, **i**
2. **Encara no està publicat** per a la data sol·licitada

…es marca com a **tren possible**.

```
Data sol·licitada: dimarts, 15 d'abril
Dates de referència: dimarts 8 abr, dim 1 abr, dim 25 mar, …

Trens en dates de referència  ──►  Unió de tots els trens vistos
                                           │
                                           ▼
                                 Trens que falten el 15 abr
                                           │
                                           ▼
                                 Marcats com a "trens possibles"
```

## A la interfície

Els trens possibles apareixen als resultats de cerca amb una **vora discontínua** i una insígnia **"Tren possible"** per distingir-los dels trens publicats confirmats. El seu preu es mostra com a "no disponible encara" ja que Renfe no l'ha publicat, però pots començar a seguir el viatge immediatament — el rastrejador començarà a comprovar tan bon punt Renfe publiqui un preu.

## Configuració

| Variable | Valor per defecte | Efecte |
|----------|-------------------|--------|
| `RENFE_POSSIBLE_TRAINS` | `1` | Establir a `0` per desactivar la inferència de trens possibles completament. |
| `RENFE_REFERENCE_WEEKS` | `10` | Nombre de setmanes del mateix dia de la setmana enrere. Més setmanes = millor cobertura però primera cerca més lenta. |

:::tip
Estableix `RENFE_REFERENCE_WEEKS=0` si només vols veure els trens publicats actualment i ometre les cerques històriques. Això fa les cerques més ràpides però desactiva tant els trens possibles com l'estimació del rang de preus.
:::
