---
id: price-range
sidebar_position: 2
title: Price Range
---

# Price Range

For every train shown in search results and on your tracked trips list, Renfe Tracker displays not just the **current price**, but also a **historical price range** — the minimum and maximum prices ever observed for that train on the same route and weekday.

## Why is this useful?

Renfe train prices fluctuate. Knowing that a ticket currently costs €45 is more actionable when you also know it has ranged from €32 to €67 in recent months. You can judge whether now is a good time to buy or whether you should wait and track the price.

## How prices are collected

The app builds its price knowledge from two sources:

### 1. Reference week lookups (search time)

When you search for a train, the app also fetches prices for the **same train on the same weekday across multiple previous weeks** (controlled by `RENFE_REFERENCE_WEEKS`, default 10). All prices found — both for the requested date and for reference dates — are stored in:

- **`price_samples`** — unique prices observed per tracked trip (used for per-trip range).
- **`price_history`** — global prices indexed by `(origin, destination, weekday, train, departure_time)` (used across all searches for that route).

### 2. Ongoing scheduler checks

Every time the price checker runs for a tracked trip, the price it finds is also recorded in both tables. Over time, this builds a richer picture of how prices move on a given route.

## Where you see it

**Search results page** — each train card shows the current price plus an estimated range:

```
AVE · 07:00 → 09:30
€ 45.10   Range: €32.00 – €67.50
```

**Tracked trips list** — the same range is shown next to the last known price for each tracked trip, so you always have context when a price change notification arrives.

## Data retention

Global price history is kept for `RENFE_PRICE_HISTORY_DAYS` days (default 365). A nightly maintenance job deletes records older than that threshold so the database doesn't grow unboundedly.

| Variable | Default | Effect |
|----------|---------|--------|
| `RENFE_REFERENCE_WEEKS` | `10` | Weeks of historical data fetched at search time |
| `RENFE_PRICE_HISTORY_DAYS` | `365` | How long global price records are retained |

:::note
Price ranges are estimates based on observed data. They reflect prices seen by the tracker on reference dates, not the full history of all prices Renfe has ever offered.
:::
