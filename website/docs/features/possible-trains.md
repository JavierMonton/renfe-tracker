---
id: possible-trains
sidebar_position: 1
title: Possible Trains
---

# Possible Trains

When you search for trains on a specific date, Renfe Tracker doesn't just show you the trains that Renfe has currently published for that day — it also shows you **trains that haven't been published yet but are very likely to run**.

## Why does this matter?

Renfe publishes train schedules progressively. A train that you know runs every Tuesday might not appear in search results yet for a date that's many weeks away. Without this feature, you'd have to keep checking back until the train shows up before you can start tracking its price.

## How it works

When you search for trains on a date, the app also fetches train schedules for the **same weekday across multiple previous weeks** (up to `RENFE_REFERENCE_WEEKS` weeks back, default 10). Any train that:

1. Ran on that weekday in at least one reference week, **and**
2. Is **not yet published** for the requested date

…is marked as a **possible train**.

```
Requested date: Tuesday, 15 April
Reference dates: Tuesday 8 Apr, Tue 1 Apr, Tue 25 Mar, …

Trains on reference dates  ──►  Union of all seen trains
                                        │
                                        ▼
                              Trains missing from 15 Apr
                                        │
                                        ▼
                              Marked as "possible trains"
```

## In the UI

Possible trains appear in search results with a **dashed border** and a **"Tren posible"** badge to distinguish them from confirmed published trains. Their price is shown as "not yet available" since Renfe hasn't published it, but you can start tracking the trip right away — the tracker will begin checking as soon as Renfe publishes a price.

## Configuration

| Variable | Default | Effect |
|----------|---------|--------|
| `RENFE_POSSIBLE_TRAINS` | `1` | Set to `0` to disable possible train inference entirely. |
| `RENFE_REFERENCE_WEEKS` | `10` | Number of same-weekday weeks to look back. More weeks = better coverage but slower first search. |

:::tip
Set `RENFE_REFERENCE_WEEKS=0` if you only want to see currently published trains and skip the historical lookups. This makes searches faster but disables both possible trains and price range estimation.
:::
