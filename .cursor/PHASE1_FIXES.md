# Phase 1.1 – Fixes (Manager-Architect)

This document defines the tasks delegated to developers to fix missing or incorrect behavior. Reference: `.cursor/Requeriments.md`.

---

## Fix 1: Expand origins and destinations list

**Owner:** Backend (search options).

**Problem:** The list of origins/destinations is very limited. Users need at least **Zaragoza**, **Calatayud**, and **Tafalla** for search.

**Acceptance criteria:**
- `GET /api/search/options` returns a list of origins and a list of destinations that **include at least** Zaragoza, Calatayud, and Tafalla, in addition to the existing cities.
- The same list is used for both origin and destination dropdowns (user can search from/to any of these stations).
- Values are consistent with what the Renfe client expects (display names; backend maps to Renfe station codes internally if needed).

**Notes:** Keep a single source of truth (e.g. a constant list in the backend). If the real Renfe API requires station codes, maintain a mapping display name ↔ code and use it in the Renfe client.

---

## Fix 2: Real train list from Renfe official website

**Owner:** Backend (Renfe client + search API).

**Problem:** The list of trains is wrong: the same mock trains and prices are shown for every search. Trains and prices must come from the **Renfe official website**, checked **on the fly** for each search.

**Requirements (from `.cursor/Requeriments.md`):**
- Original website: https://www.renfe.com/es/es (ticket search may be on venta.renfe.com).
- Search inputs: date (one-way), origin, destination, 1 adult. No round trip, no passenger count.
- The site may require cookies or session to search properly.
- Results must show available trains and their **real** prices (and duration, train type e.g. AVE, Alvia).

**Acceptance criteria:**
- When the user submits a search (date, origin, destination), the backend **calls the Renfe official website** (or its ticket-sale endpoint), performs a real search with those parameters, and parses the response.
- The API returns the **actual** list of trains and prices returned by Renfe for that date/origin/destination (no mock data).
- If Renfe is unreachable or returns an error, the API responds with an appropriate HTTP status (e.g. 502/503) and a clear error message; the frontend can show "No se pudieron cargar los trenes. Inténtalo más tarde."
- Session/cookies are handled so that the Renfe search succeeds when the site requires it.
- Estimated price range and "possible trains" (from requirements) can be left for a later phase; this fix is only about **real** trains and **real** prices from Renfe.

**Technical notes:**
- Use the existing stack: httpx for HTTP, and add BeautifulSoup (or similar) for HTML parsing if the response is HTML. If the Renfe site uses JavaScript to load results, consider Playwright (or document the limitation and add it in a follow-up).
- Map frontend origin/destination display names to whatever Renfe expects (station codes/IDs) inside the client.
- Do not fall back to mock data when the user has requested a real search; return real data or an error.

---

## Summary for developers

| Fix | Component | Action |
|-----|-----------|--------|
| 1   | `app/api/search.py` (options) | Extend origins/destinations list to include at least Zaragoza, Calatayud, Tafalla. |
| 2   | `app/renfe_client.py` + deps | Replace stub with real Renfe website client: perform search on the fly, parse response, return real trains and prices; handle errors without returning mock data. |

After both fixes, the user can select Zaragoza/Calatayud/Tafalla and see **real** trains and prices from Renfe for the chosen date and route.

---

## Implementation status

- **Fix 1:** Done. Origins/destinations in `app/api/search.py` now include Zaragoza, Calatayud, Tafalla.
- **Fix 2:** Done. `app/renfe_client.py` implements a real client: session with cookies, POST to venta.renfe.com, HTML parsing with BeautifulSoup. If Renfe’s form uses different field names or the results are loaded via JavaScript, the client may need tuning (form parameters or Playwright) after testing against the live site. On failure the API returns 503 with a clear message; the frontend shows it in the alert.
