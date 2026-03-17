"""
Possible trains: infer trains that typically run on the same weekday but are not
yet published by Renfe for the requested date. Uses 1–2 reference dates (same
weekday, near today) and get_train_prices for requested + reference dates.
"""
import logging
import os
from datetime import date, timedelta
from typing import Any

from app.renfe_lib import get_train_prices

logger = logging.getLogger(__name__)


def _get_max_reference_weeks() -> int:
    """
    Number of same-weekday reference weeks to use for price estimation.

    Controlled by RENFE_REFERENCE_WEEKS env var (default: 10).
    Must be >= 0. If set to 0, only the requested date is used.
    """
    raw = os.environ.get("RENFE_REFERENCE_WEEKS", "").strip()
    if not raw:
        return 10
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Invalid RENFE_REFERENCE_WEEKS=%r; falling back to 10", raw)
        return 10
    if value < 0:
        logger.warning("RENFE_REFERENCE_WEEKS=%r is negative; using 0", raw)
        return 0
    return value


def _train_key(t: dict[str, Any]) -> tuple[str, str]:
    """Unique key for a train: (train_type, departure_time HH:MM)."""
    return (t["train_type"], t["departure_time"])


def _collect_prices_by_key(results: list[dict[str, Any]]) -> dict[tuple[str, str], list[float]]:
    """From raw get_train_prices results, collect available prices by train key."""
    by_key: dict[tuple[str, str], list[float]] = {}
    for t in results:
        if not t.get("available"):
            continue
        price = t.get("price")
        if price is None:
            continue
        try:
            p = float(price)
        except (TypeError, ValueError):
            continue
        key = _train_key(t)
        by_key.setdefault(key, []).append(p)
    return by_key


def _merge_prices_into(
    into: dict[tuple[str, str], list[float]],
    results: list[dict[str, Any]],
) -> None:
    """Merge available prices from results into the given dict (mutates into)."""
    for key, prices in _collect_prices_by_key(results).items():
        into.setdefault(key, []).extend(prices)


def _price_ranges_by_key(
    prices_by_key: dict[tuple[str, str], list[float]],
) -> dict[tuple[str, str], tuple[float | None, float | None]]:
    """For each key with at least one price, return (min, max). Otherwise (None, None)."""
    out: dict[tuple[str, str], tuple[float | None, float | None]] = {}
    for key, prices in prices_by_key.items():
        if not prices:
            out[key] = (None, None)
        else:
            out[key] = (min(prices), max(prices))
    return out


def _reference_dates(requested_date_str: str, max_dates: int | None = None) -> list[str]:
    """
    Compute up to max_dates reference dates: same weekday as requested_date,
    preferably in [today, requested_date). If the next same-weekday from today
    is the requested date, use the previous 1–2 same-weekday dates instead.
    """
    requested = date.fromisoformat(requested_date_str)
    if max_dates is None:
        max_dates = _get_max_reference_weeks()
    if max_dates <= 0:
        return []
    today = date.today()
    if requested < today:
        return []
    ref_weekday = requested.weekday()
    ref_dates: list[str] = []

    # Next same-weekday from today (could be today)
    days_ahead = (ref_weekday - today.weekday() + 7) % 7
    first_candidate = today + timedelta(days=days_ahead)

    if first_candidate < requested:
        # Use same-weekday dates before requested (next 1–2 occurrences from today)
        d = first_candidate
        while d < requested and len(ref_dates) < max_dates:
            ref_dates.append(d.isoformat())
            d += timedelta(days=7)
    else:
        # Next same-weekday from today is the requested date; use previous same-weekday dates
        for k in range(1, max_dates + 1):
            d = requested - timedelta(days=7 * k)
            ref_dates.append(d.isoformat())

    return ref_dates[:max_dates]


def _raw_to_api_train(
    t: dict[str, Any],
    *,
    is_possible: bool = False,
    inferred_from_date: str | None = None,
    estimated_price_min: float | None = None,
    estimated_price_max: float | None = None,
    estimated_prices: list[float] | None = None,
) -> dict[str, Any]:
    """Convert raw get_train_prices item to API shape; add is_possible, optional inferred_from_date, and price range."""
    out: dict[str, Any] = {
        "name": t["train_type"],
        "price": t["price"] if t.get("available") else None,
        "duration_minutes": t["duration_minutes"],
        "estimated_price_min": estimated_price_min,
        "estimated_price_max": estimated_price_max,
        "estimated_prices": estimated_prices if estimated_prices is not None else [],
        "is_possible": is_possible,
        "departure_time": t["departure_time"],
    }
    if inferred_from_date is not None:
        out["inferred_from_date"] = inferred_from_date
    return out


def get_trains_with_possible(
    origin: str,
    destination: str,
    requested_date: str,
) -> list[dict[str, Any]]:
    """
    Return trains for (origin, destination, requested_date): real trains first
    (is_possible=False), then possible trains (is_possible=True, inferred_from_date
    set). Uses get_train_prices for requested date and up to 2 reference dates.
    On requested-date failure, raises. On reference-date failure, logs and skips.
    """
    # Requested date: must succeed
    try:
        requested_results = get_train_prices(origin, destination, requested_date, page=1, per_page=50)
    except Exception as e:
        logger.exception("get_train_prices failed for requested date %s: %s", requested_date, e)
        raise

    real_keys = {_train_key(t) for t in requested_results}

    # Collect available prices by train key from requested date and reference dates (same weekday)
    prices_by_key: dict[tuple[str, str], list[float]] = {}
    _merge_prices_into(prices_by_key, requested_results)

    ref_dates = _reference_dates(requested_date)
    possible_by_key: dict[tuple[str, str], dict[str, Any]] = {}

    for ref_date in ref_dates:
        try:
            ref_results = get_train_prices(origin, destination, ref_date, page=1, per_page=50)
        except Exception as e:
            logger.warning("get_train_prices failed for reference date %s: %s", ref_date, e)
            continue
        _merge_prices_into(prices_by_key, ref_results)
        for t in ref_results:
            key = _train_key(t)
            if key not in real_keys and key not in possible_by_key:
                possible_by_key[key] = _raw_to_api_train(
                    t, is_possible=True, inferred_from_date=ref_date
                )

    price_ranges = _price_ranges_by_key(prices_by_key)

    real_trains = [
        _raw_to_api_train(
            t,
            is_possible=False,
            estimated_price_min=price_ranges.get(_train_key(t), (None, None))[0],
            estimated_price_max=price_ranges.get(_train_key(t), (None, None))[1],
            estimated_prices=list(prices_by_key.get(_train_key(t), [])),
        )
        for t in requested_results
    ]
    real_trains.sort(key=_dep_sort_key)

    for key, train in possible_by_key.items():
        emin, emax = price_ranges.get(key, (None, None))
        train["estimated_price_min"] = emin
        train["estimated_price_max"] = emax
        train["estimated_prices"] = list(prices_by_key.get(key, []))

    possible_list = list(possible_by_key.values())
    possible_list.sort(key=_dep_sort_key)

    return real_trains + possible_list


def _dep_sort_key(train: dict[str, Any]) -> str:
    """Sort key by departure time (HH:MM)."""
    return train.get("departure_time", "99:99")