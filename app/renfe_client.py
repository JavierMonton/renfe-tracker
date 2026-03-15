"""
Renfe client: simula una sesión real de navegación en la web de Renfe para obtener
resultados de búsqueda (trenes y precios). Usa Playwright para manejar sesión/cookies y JS.
Ver .cursor/Requeriments.md.
"""
import asyncio
import logging
import re
from typing import List

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger("renfe_tracker.renfe_client")

# Tiempo máximo para cargar página, rellenar formulario y ver resultados.
# La búsqueda en Renfe son varias peticiones; es normal que tarde 1-3 minutos.
PAGE_TIMEOUT_MS = 180_000  # 3 minutos

# URL de búsqueda de Renfe (venta).
RENFE_BUSCAR = "https://venta.renfe.com/vol/buscarTren.do"


class RenfeClientError(Exception):
    """Error cuando Renfe no está disponible o no se pueden obtener los trenes."""

    pass


class RenfeBrowserNotFoundError(RenfeClientError):
    """Chromium/Playwright no está instalado (ej. ejecutable no existe)."""

    pass


class RenfeTimeoutError(RenfeClientError):
    """La búsqueda en Renfe superó el tiempo máximo."""

    pass


def _format_date_for_renfe(date: str) -> str:
    """Convierte YYYY-MM-DD a dd/MM/yyyy para el formulario Renfe."""
    if re.match(r"\d{4}-\d{2}-\d{2}", date):
        y, m, d = date.split("-")
        return f"{d}/{m}/{y}"
    return date


def _parse_price_eur(text: str) -> float | None:
    """Extrae precio en euros de texto como '45,60 €' o '45.60€'."""
    if not text:
        return None
    cleaned = text.replace(",", ".").replace(" ", "").replace("€", "").strip()
    match = re.search(r"(\d+\.?\d*)", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _parse_duration_minutes(text: str) -> int | None:
    """Parsea duración en texto tipo '2h 30min' o '150 min'."""
    if not text:
        return None
    total = 0
    h = re.search(r"(\d+)\s*h", text, re.I)
    if h:
        total += 60 * int(h.group(1))
    m = re.search(r"(\d+)\s*m", text, re.I)
    if m:
        total += int(m.group(1))
    only_m = re.search(r"^(\d+)\s*min", text.strip(), re.I)
    if only_m and total == 0:
        total = int(only_m.group(1))
    return total if total else None


def _parse_trains_from_html(html: str) -> List[dict]:
    """Extrae lista de trenes del HTML de la página de resultados. Misma estructura que antes."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    trains = []
    price_eur_re = re.compile(r"\d+[,.]?\d*\s*€")
    train_type_re = re.compile(
        r"\b(AVE|Alvia|Avlo|Intercity|InterCity|MD|Regional|Tren Hotel)\b", re.I
    )

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
        name = "Tren"
        for m in train_type_re.finditer(text):
            name = m.group(0)
            break
        if name == "Tren":
            for cell in cells:
                t = cell.get_text(strip=True)
                if t and not price_eur_re.search(t) and len(t) < 80:
                    name = t[:60]
                    break
        duration = _parse_duration_minutes(text) or 0
        trains.append({
            "name": name,
            "price": price,
            "duration_minutes": duration,
            "estimated_price_min": None,
            "estimated_price_max": None,
        })

    if not trains:
        for block in soup.find_all(
            ["div", "li"], class_=re.compile(r"tren|train|result|viaje|journey", re.I)
        ):
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


async def search_trains(date: str, origin: str, destination: str) -> List[dict]:
    """
    Navega en la web de Renfe como un usuario real (sesión, cookies, formulario),
    realiza la búsqueda y devuelve la lista de trenes con precios.
    Lanza RenfeClientError si la web no responde o no se pueden obtener resultados.
    """
    fecha = _format_date_for_renfe(date)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    locale="es-ES",
                    timezone_id="Europe/Madrid",
                    viewport={"width": 1280, "height": 720},
                )
                context.set_default_timeout(PAGE_TIMEOUT_MS)
                page = await context.new_page()

                try:
                    # 1) Ir a la página de búsqueda para establecer sesión
                    await page.goto(RENFE_BUSCAR, wait_until="domcontentloaded")
                    await page.wait_for_load_state("networkidle", timeout=PAGE_TIMEOUT_MS)

                    # 2) Rellenar formulario. Renfe puede usar <select> (estaciones) o inputs con autocompletado.
                    # Origen
                    sel_origin = page.locator("select[name*='origen'], select[id*='origen']").first
                    if await sel_origin.count() > 0:
                        await sel_origin.select_option(label=origin)
                    else:
                        origin_input = page.get_by_label("Origen").or_(page.locator("input[name*='origen']").first)
                        await origin_input.fill(origin)
                        await page.wait_for_timeout(600)
                        try:
                            await page.locator("li, [role=option]").filter(has_text=re.compile(re.escape(origin), re.I)).first.click(timeout=3000)
                        except PlaywrightTimeout:
                            pass

                    # Destino
                    sel_dest = page.locator("select[name*='destino'], select[id*='destino']").first
                    if await sel_dest.count() > 0:
                        await sel_dest.select_option(label=destination)
                    else:
                        dest_input = page.get_by_label("Destino").or_(page.locator("input[name*='destino']").first)
                        await dest_input.fill(destination)
                        await page.wait_for_timeout(600)
                        try:
                            await page.locator("li, [role=option]").filter(has_text=re.compile(re.escape(destination), re.I)).first.click(timeout=3000)
                        except PlaywrightTimeout:
                            pass

                    # Fecha ida (solo ida)
                    date_input = page.get_by_label("Fecha").or_(page.locator("input[name*='fecha'], input[name*='ida'], input[type=date]").first)
                    await date_input.fill(fecha)

                    # 3) Enviar búsqueda
                    buscar = page.get_by_role("button", name=re.compile(r"Buscar|Comprar|Consultar|Search", re.I)).or_(
                        page.locator("input[type=submit], button[type=submit]").first
                    )
                    await buscar.click()

                    # 4) Esperar a que aparezcan resultados (tabla o lista de trenes)
                    await page.wait_for_load_state("networkidle", timeout=PAGE_TIMEOUT_MS)
                    # Selector genérico: algo que contenga precios o filas de trenes
                    await page.wait_for_selector("tr, [class*='tren'], [class*='result'], [class*='viaje'], table", timeout=90_000)

                    html = await page.content()
                except PlaywrightTimeout as e:
                    logger.warning("Playwright timeout en Renfe: %s", e)
                    raise RenfeTimeoutError("Renfe tardó demasiado en responder.") from e
                finally:
                    await context.close()
            finally:
                await browser.close()
    except Exception as e:
        msg = str(e).lower()
        if "executable doesn't exist" in msg or ("playwright" in msg and "chromium" in msg):
            raise RenfeBrowserNotFoundError(
                "Renfe no disponible: navegador no instalado. Ejecuta 'playwright install chromium' o usa Docker."
            ) from e
        if isinstance(e, RenfeClientError):
            raise
        raise RenfeClientError(str(e)) from e

    trains = _parse_trains_from_html(html)
    if not trains and "renfe" in html.lower():
        raise RenfeClientError(
            "Renfe respondió pero no se encontraron trenes para esa fecha y trayecto, o la estructura de la página ha cambiado."
        )
    return trains
