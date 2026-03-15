"""
Possible trains: infer trains that typically run on the same weekday but are not
yet published by Renfe for the requested date. Uses 1–2 reference dates (same
weekday, near today) and get_train_prices for requested + reference dates.
"""
import logging
from datetime import date, timedelta
from typing import Any

from app.renfe_lib import get_train_prices

logger = logging.getLogger(__name__)

MAX_REFERENCE_DATES = 2


def _train_key(t: dict[str, Any]) -> tuple[str, str]:
    """Unique key for a train: (train_type, departure_time HH:MM)."""
    return (t["train_type"], t["departure_time"])


def _reference_dates(requested_date_str: str, max_dates: int = MAX_REFERENCE_DATES) -> list[str]:
    """
    Compute up to max_dates reference dates: same weekday as requested_date,
    preferably in [today, requested_date). If the next same-weekday from today
    is the requested date, use the previous 1–2 same-weekday dates instead.
    """
    requested = date.fromisoformat(requested_date_str)
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
) -> dict[str, Any]:
    """Convert raw get_train_prices item to API shape; add is_possible and optional inferred_from_date."""
    out: dict[str, Any] = {
        "name": t["train_type"],
        "price": t["price"] if t.get("available") else None,
        "duration_minutes": t["duration_minutes"],
        "estimated_price_min": None,
        "estimated_price_max": None,
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
    real_trains = [
        _raw_to_api_train(t, is_possible=False)
        for t in requested_results
    ]
    real_trains.sort(key=_dep_sort_key)

    # Possible trains from reference dates
    ref_dates = _reference_dates(requested_date)
    possible_by_key: dict[tuple[str, str], dict[str, Any]] = {}

    for ref_date in ref_dates:
        try:
            ref_results = get_train_prices(origin, destination, ref_date, page=1, per_page=50)
        except Exception as e:
            logger.warning("get_train_prices failed for reference date %s: %s", ref_date, e)
            continue
        for t in ref_results:
            key = _train_key(t)
            if key not in real_keys and key not in possible_by_key:
                possible_by_key[key] = _raw_to_api_train(
                    t, is_possible=True, inferred_from_date=ref_date
                )

    possible_list = list(possible_by_key.values())
    possible_list.sort(key=_dep_sort_key)

    return real_trains + possible_list


def _dep_sort_key(train: dict[str, Any]) -> str:
    """Sort key by departure time (HH:MM)."""
    return train.get("departure_time", "99:99")