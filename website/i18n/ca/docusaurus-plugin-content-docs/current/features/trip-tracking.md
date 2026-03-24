---
id: trip-tracking
sidebar_position: 3
title: Seguiment de Viatges
---

# Seguiment de Viatges

El seguiment de viatges és la funció principal de Renfe Tracker. Un cop trobes un tren que t'interessa, pots **seguir-lo** — l'aplicació comprovarà el preu periòdicament i registrarà cada canvi, perquè sempre sàpigues quan comprar.

## Afegir un viatge seguit

1. Ves a la pàgina de **Cerca** i introdueix el teu origen, destinació i data de viatge.
2. Troba el tren que vols als resultats.
3. Fes clic a **Seguir** per obrir el diàleg de seguiment.
4. Tria un **interval de comprovació** (amb quina freqüència ha de comprovar el preu l'aplicació).
5. Confirma — el viatge ja s'està seguint.

Pots seguir la mateixa ruta amb diferents trens, o el mateix tren en múltiples dates, com a viatges seguits separats.

## Com funciona la comprovació de preus

L'aplicació executa un treball del planificador **cada minut**. Per a cada viatge seguit que hagi de ser comprovat (segons el seu interval configurat):

1. Consulta a Renfe el preu actual d'aquell tren específic.
2. Arrodoneix el preu a 2 decimals (usant ROUND_HALF_UP).
3. Compara amb el darrer preu registrat.
4. Si el preu ha canviat:
   - Registra un **esdeveniment de preu** (marca de temps + nou preu).
   - Actualitza la direcció del canvi de preu (`pujada` / `baixada`).
   - Envia les [notificacions](./notifications) configurades.
5. Sempre actualitza `last_checked_at` i registra el preu a les mostres històriques.

## Veure l'historial de preus

Fes clic a qualsevol viatge seguit a la pàgina d'inici per obrir la seva **pàgina de detall**. Veuràs una línia de temps cronològica de cada canvi de preu detectat, amb fletxes que indiquen si el preu va pujar o baixar i en quant.

## Interval de comprovació

L'interval de comprovació és configurable per viatge. Els intervals més curts signifiquen una detecció més ràpida però més consultes a Renfe. Considera:

- **5–15 minuts** per a viatges on esperes canvis de preu ràpids (p. ex. a prop de la data de viatge).
- **1–4 hores** per a viatges llunyans en el futur on les fluctuacions diàries són més comunes.

## Gestionar viatges seguits

Des de la pàgina d'inici pots:

- **Veure** l'historial de preus de qualsevol viatge seguit.
- **Eliminar** un viatge que ja no vols seguir.

Els viatges estan agrupats per ruta a la pàgina d'inici per facilitar la visualització.

:::info
Els trens possibles (encara no publicats per Renfe) també es poden seguir. El comprovador de preus simplement no trobarà preu fins que Renfe publiqui el tren, moment en el qual el primer preu es registra com a valor inicial i el seguiment comença normalment.
:::
