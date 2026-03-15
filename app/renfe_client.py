"""
Renfe client: query the official Renfe website for real train search results.
Uses httpx for HTTP and BeautifulSoup for HTML parsing. Handles session/cookies.
See .cursor/Requeriments.md and .cursor/PHASE1_FIXES.md.
"""
import logging
import re
from typing import List

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("renfe_tracker.renfe_client")

# Timeout for requests to Renfe (site can be slow).
RENFE_TIMEOUT = 30.0

# User-Agent similar to a browser so the site is more likely to accept the request.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Base URL for ticket search (Renfe venta).
RENFE_VENTA_BASE = "https://venta.renfe.com"


class RenfeClientError(Exception):
    """Raised when the Renfe site is unreachable or response cannot be parsed."""

    pass


def _format_date_for_renfe(date: str) -> str:
    """Convert YYYY-MM-DD to dd/MM/yyyy for Renfe form if needed."""
    if re.match(r"\d{4}-\d{2}-\d{2}", date):
        parts = date.split("-")
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return date


def _parse_price_eur(text: str) -> float | None:
    """Extract a price in euros from text like '45,60 €' or '45.60€'."""
    if not text:
        return None
    # Replace comma with dot, remove spaces and €
    cleaned = text.replace(",", ".").replace(" ", "").replace("€", "").strip()
    match = re.search(r"(\d+\.?\d*)", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _parse_duration_minutes(text: str) -> int | None:
    """Parse duration from text like '2h 30min' or '150 min'."""
    if not text:
        return None
    total = 0
    h = re.search(r"(\d+)\s*h", text, re.I)
    if h:
        total += 60 * int(h.group(1))
    m = re.search(r"(\d+)\s*m", text, re.I)
    if m:
        total += int(m.group(1))
    # Only minutes
    only_m = re.search(r"^(\d+)\s*min", text.strip(), re.I)
    if only_m and total == 0:
        total = int(only_m.group(1))
    return total if total else None


def _parse_search_results(html: str) -> List[dict]:
    """
    Parse Renfe search result HTML into list of train dicts.
    Returns list with keys: name, price, duration_minutes, estimated_price_min, estimated_price_max.
    estimated_* can be None for now (Phase 2). If no trains found or structure unknown, returns [].
    """
    soup = BeautifulSoup(html, "html.parser")
    trains = []

    # Renfe often uses tables or divs with train info. Try common patterns.
    # Look for rows/cards that contain price (€) and train type (AVE, Alvia, etc.).
    price_eur_re = re.compile(r"\d+[,.]?\d*\s*€")
    train_type_re = re.compile(r"\b(AVE|Alvia|Avlo|Intercity|InterCity|Alvia|MD|Regional|Tren Hotel)\b", re.I)

    # Strategy 1: table rows with a cell containing €
    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])
        text = row.get_text(separator=" ", strip=True)
        if not price_eur_re.search(text):
            continue
        price = None
        for cell in cells:
            p = _parse_price_eur(cell.get_text())
            if p is not None:
                price = p
                break
        if price is None:
            price = _parse_price_eur(text)
        name = None
        for m in train_type_re.finditer(text):
            name = m.group(0)
            break
        if not name:
            # Use first non-empty cell or a snippet
            for cell in cells:
                t = cell.get_text(strip=True)
                if t and not price_eur_re.search(t) and len(t) < 80:
                    name = t[:60]
                    break
        if name is None:
            name = "Tren"
        duration = _parse_duration_minutes(text) or 0
        trains.append({
            "name": name,
            "price": price,
            "duration_minutes": duration,
            "estimated_price_min": None,
            "estimated_price_max": None,
        })

    # Strategy 2: if no table rows, look for divs/cards with data attributes or classes
    if not trains:
        for block in soup.find_all(["div", "li"], class_=re.compile(r"tren|train|result|viaje|journey", re.I)):
            text = block.get_text(separator=" ", strip=True)
            if not price_eur_re.search(text):
                continue
            price = _parse_price_eur(text)
            if price is None:
                continue
            name = "Tren"
            for m in train_type_re.finditer(text):
                name = m.group(0)
                break
            duration = _parse_duration_minutes(text) or 0
            trains.append({
                "name": name,
                "price": price,
                "duration_minutes": duration,
                "estimated_price_min": None,
                "estimated_price_max": None,
            })

    return trains


def search_trains(date: str, origin: str, destination: str) -> List[dict]:
    """
    Search the Renfe official website for trains for the given date, origin and destination.
    Returns list of dicts with keys: name, price, duration_minutes, estimated_price_min, estimated_price_max.
    Raises RenfeClientError if the site is unreachable or response cannot be used.
    """
    with httpx.Client(
        follow_redirects=True,
        timeout=RENFE_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        try:
            # 1) Get initial page to obtain session cookies
            get_resp = client.get(f"{RENFE_VENTA_BASE}/vol/searchTickets.do")
            get_resp.raise_for_status()

            # 2) Submit search. Renfe venta often uses POST with form data.
            # Field names may vary; common ones: origen, destino, fechaIda, idaVuelta, numAdultos
            fecha = _format_date_for_renfe(date)
            form_data = {
                "origen": origin,
                "destino": destination,
                "fechaIda": fecha,
                "idaVuelta": "0",
                "numAdultos": "1",
            }
            # Some Renfe endpoints expect specific parameter names; adjust if 400/500
            post_resp = client.post(
                f"{RENFE_VENTA_BASE}/vol/searchTickets.do",
                data=form_data,
                headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
            )
            post_resp.raise_for_status()
            html = post_resp.text

        except httpx.HTTPError as e:
            logger.warning("Renfe request failed: %s", e)
            raise RenfeClientError(f"No se pudo conectar con Renfe: {e!s}") from e

    trains = _parse_search_results(html)
    # If we got a valid HTML but no parsed trains, the page structure may have changed
    if not trains and "renfe" in html.lower():
        logger.warning("Renfe returned HTML but no trains could be parsed; page structure may have changed.")
        raise RenfeClientError(
            "Renfe respondió pero no se pudieron obtener los trenes. La estructura de la página puede haber cambiado."
        )
    return trains
