from datetime import date as _date
from unittest.mock import patch


def _fake_date_class(fixed_today: _date):
    class FakeDate(_date):
        @classmethod
        def today(cls):  # type: ignore[override]
            return fixed_today

    return FakeDate


def test_reference_dates_next_weekday_fills_after_requested():
    """
    If the requested date is the next occurrence of that weekday from today,
    there are no same-weekday dates in [today, requested). We should still
    return future weeks after the requested date to build a useful range.
    """
    fixed_today = _date(2026, 3, 16)  # Monday
    requested = "2026-03-20"  # Friday (next Friday from fixed_today)

    from app.services import possible_trains as pt

    with patch.object(pt, "date", _fake_date_class(fixed_today)):
        refs = pt._reference_dates(requested, max_dates=10)

    assert len(refs) == 10
    assert refs[0] == "2026-03-27"
    assert refs[-1] == "2026-05-29"


def test_reference_dates_far_future_prefers_between_today_and_requested():
    fixed_today = _date(2026, 3, 16)  # Monday
    requested = "2026-05-22"  # Friday, far enough out

    from app.services import possible_trains as pt

    with patch.object(pt, "date", _fake_date_class(fixed_today)):
        refs = pt._reference_dates(requested, max_dates=10)

    # First 10 Fridays starting at the next Friday after today, all < requested
    assert refs == [
        "2026-03-20",
        "2026-03-27",
        "2026-04-03",
        "2026-04-10",
        "2026-04-17",
        "2026-04-24",
        "2026-05-01",
        "2026-05-08",
        "2026-05-15",
        "2026-05-29",
    ]


def test_reference_dates_past_requested_returns_empty():
    fixed_today = _date(2026, 3, 16)
    requested = "2026-03-01"

    from app.services import possible_trains as pt

    with patch.object(pt, "date", _fake_date_class(fixed_today)):
        refs = pt._reference_dates(requested, max_dates=10)

    assert refs == []

