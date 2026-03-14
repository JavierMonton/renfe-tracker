"""Renfe client (stub). Returns mock train data for any search."""
from typing import Any, List

def search_trains(date: str, origin: str, destination: str) -> List[dict]:
    """Stub: return 2–3 mock trains (name, price, duration, optional estimated_price_min/max)."""
    return [
        {
            "name": "AVE 0101",
            "price": 45.50,
            "duration_minutes": 165,
            "estimated_price_min": 42.00,
            "estimated_price_max": 52.00,
        },
        {
            "name": "Alvia 0122",
            "price": 38.20,
            "duration_minutes": 210,
            "estimated_price_min": 35.00,
            "estimated_price_max": 44.00,
        },
        {
            "name": "AVE 0145",
            "price": 52.00,
            "duration_minutes": 150,
            "estimated_price_min": 48.00,
            "estimated_price_max": 58.00,
        },
    ]
