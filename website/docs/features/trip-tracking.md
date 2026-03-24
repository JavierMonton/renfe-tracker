---
id: trip-tracking
sidebar_position: 3
title: Trip Tracking
---

# Trip Tracking

Trip tracking is the core feature of Renfe Tracker. Once you find a train you're interested in, you can **track it** — the app will periodically check the price and record every change, so you always know when to buy.

## Adding a tracked trip

1. Go to the **Search** page and enter your origin, destination, and travel date.
2. Find the train you want in the results.
3. Click **Track** to open the tracking dialog.
4. Choose a **check interval** (how often the app should check the price).
5. Confirm — the trip is now being tracked.

You can track the same route with different trains, or the same train on multiple dates, as separate tracked trips.

## How price checking works

The app runs a scheduler job **every minute**. For each tracked trip that is due for a check (based on its configured interval), it:

1. Queries Renfe for the current price of that specific train.
2. Rounds the price to 2 decimal places (using ROUND_HALF_UP).
3. Compares with the last recorded price.
4. If the price has changed:
   - Records a **price event** (timestamp + new price).
   - Updates the price change direction (`up` / `down`).
   - Dispatches any configured [notifications](./notifications).
5. Always updates `last_checked_at` and records the price in the historical samples.

## Viewing price history

Click any tracked trip on the home page to open its **detail page**. You'll see a chronological timeline of every price change detected, with arrows indicating whether the price went up or down and by how much.

## Check interval

The check interval is configurable per trip. Shorter intervals mean faster detection but more Renfe queries. Consider:

- **5–15 minutes** for trips where you expect rapid price changes (e.g. close to travel date).
- **1–4 hours** for trips far in the future where daily fluctuations are more common.

## Managing tracked trips

From the home page you can:

- **View** the price history of any tracked trip.
- **Delete** a trip you no longer want to track.

Trips are grouped by route on the home page for easy scanning.

:::info
Possible trains (not yet published by Renfe) can be tracked too. The price checker will simply find no price until Renfe publishes the train, at which point the first price is recorded as the initial value and tracking begins normally.
:::
