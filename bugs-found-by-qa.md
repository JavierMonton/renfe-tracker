# Bugs found by QA

Reporte generado para que el manager-architect pueda crear tareas. Detalle de pasos, llamadas y causas probables.

**Note:** The app now uses only the **in-process Renfe library** (GTFS + DWR scraper via `app.renfe_lib`). The Playwright/Chromium backend has been removed. Bugs 2 and 3 below are **obsolete** for the Playwright scenario (no browser); 503 can still occur if the Renfe site or DWR service is unavailable, but the previous browser/timeout causes no longer apply.

---

## Bug 1: Mensaje de búsqueda visible antes de pulsar Search

**Severidad:** Media (UX).

**Pasos para reproducir:**
1. Abrir http://localhost:8000
2. Ir a "Track new trip" (vista de búsqueda)
3. No pulsar aún el botón "Search"

**Esperado:** Solo se ve el formulario (fecha, origen, destino) y el botón "Search". No debe mostrarse el texto "Consultando Renfe…" ni el spinner hasta que el usuario pulse Search.

**Actual:** El mensaje de carga ("Consultando Renfe… La búsqueda puede tardar 1-2 minutos.") y/o el spinner aparecen antes de pulsar Search.

**Causa probable:** El bloque `#search-loading` tiene `hidden` en el HTML pero (1) no se resetea al entrar en la vista de búsqueda, o (2) en algunos navegadores `display: flex` puede hacer que el elemento ocupe espacio o sea visible aunque tenga `hidden`. También es posible que el botón quedara en estado "Buscando…" y deshabilitado si el usuario salió de la vista antes de que terminara una petición anterior.

**Llamadas/respuestas:** N/A (bug de estado de la UI).

**Estado:** Corregido en esta pasada: se resetea el estado de carga al entrar en la vista de búsqueda (loading oculto, botón "Search" y habilitado) y se añade `.search-loading[hidden] { display: none !important; }` para garantizar que no se muestre.

---

## Bug 2: Llamadas del frontend al backend devuelven 503

**Severidad:** Alta (la búsqueda no funciona).

**Pasos para reproducir:**
1. Abrir http://localhost:8000
2. Ir a búsqueda, elegir fecha / origen / destino (p. ej. Madrid → Barcelona, mañana)
3. Pulsar "Search"
4. Abrir DevTools → pestaña Network
5. Observar la petición `POST /api/search`

**Esperado:** La petición devuelve 200 y un JSON con `{ "trains": [ ... ] }`.

**Actual:** La petición tarda mucho (hasta minutos) y termina en **503 Service Unavailable**. El cuerpo de la respuesta suele incluir un `detail` con mensaje de error de Renfe (p. ej. timeout o "No se pudo conectar con Renfe").

**Otras llamadas:** 
- `GET /api/search/options` y `GET /api/trips` no deberían devolver 503 (no usan Renfe). Si se observa 503 en ellas, podría ser que el servidor esté caído o que haya un proxy/gateway delante.
- La que falla de forma consistente es **POST /api/search**, porque esa es la que llama al cliente Renfe (Playwright + venta.renfe.com).

**Causa raíz (backend):** El backend usa Playwright para abrir la web de Renfe, rellenar el formulario y extraer resultados. Cualquiera de estos fallos produce 503:

1. **Chromium no instalado:** Si la app se ejecuta fuera de Docker (p. ej. `uvicorn` en local) y no se ha ejecutado `playwright install chromium`, Playwright lanza algo como:  
   `Executable doesn't exist at .../chromium_headless_shell.../chrome-headless-shell`  
   Eso se traduce en excepción en el cliente → API devuelve 503.

2. **Timeout:** Renfe tarda más de lo configurado (p. ej. 3 min) en cargar o en mostrar resultados → `RenfeClientError` → 503.

3. **Estructura de la página distinta:** Si venta.renfe.com ha cambiado (selectores, nombres de campos, flujo), el script no encuentra origen/destino/fecha o la tabla de resultados → timeout o HTML sin trenes → 503.

4. **Renfe bloquea o no responde:** Captcha, restricción por IP o caída del sitio → fallo en el cliente → 503.

**Comprobación realizada (sin Docker):** Se ejecutó `search_trains('2025-06-15', 'Madrid', 'Barcelona')` en local. Error obtenido:  
`BrowserType.launch: Executable doesn't exist at .../chromium_headless_shell...`  
Es decir, en entornos donde no se ha instalado Chromium (o no se usa la imagen Docker con Chromium), **todas** las búsquedas fallan con 503.

**Recomendaciones para el manager-architect:**
- Asegurar que en producción/desarrollo la app corre donde Chromium está instalado (p. ej. con `docker compose up` según el Dockerfile actual).
- Si se quiere poder probar sin Renfe real: añadir un modo "mock" (variable de entorno) que devuelva datos de ejemplo y no lance Playwright, para que el frontend y el flujo se prueben sin depender de la web de Renfe.
- Revisar con backend si los selectores y el flujo en `app/renfe_client.py` siguen siendo válidos para la página actual de venta.renfe.com (origen, destino, fecha, botón, tabla de resultados).

---

## Bug 3: La búsqueda tarda mucho y acaba en 503. ¿Funciona el backend?

**Severidad:** Alta (funcionalidad core).

**Pasos para reproducir:** Los mismos que en Bug 2.

**Esperado:** En 1–3 minutos la búsqueda termina y se muestran trenes, o un mensaje claro si no hay resultados para esa fecha/trayecto.

**Actual:** La petición se alarga y termina en 503. No está claro si el backend llega a abrir Renfe o falla antes (p. ej. al lanzar el navegador).

**Conclusión QA:** El backend **sí está preparado** para hacer la búsqueda (Playwright, venta.renfe.com, timeouts de 3 min), pero **falla en la práctica** por al menos una de estas razones:

- **Entorno:** Chromium no está instalado donde corre la app (muy probable en desarrollo local sin Docker).
- **Renfe:** La web de Renfe no responde, cambia de estructura o bloquea el acceso.
- **Selectores/flujo:** El HTML de venta.renfe.com no coincide con lo que espera `renfe_client.py` (formulario o resultados).

Para confirmar si "funciona en algún escenario": ejecutar la app **con Docker** (`docker compose up --build`), que incluye Chromium, y repetir una búsqueda mientras se observa la pestaña Network y, si es posible, logs del contenedor. Si sigue 503, revisar el mensaje en `detail` y los logs del backend para distinguir timeout vs. error de Playwright vs. HTML no parseable.

---

## Resumen para el manager-architect

| Bug | Resumen | Acción sugerida |
|-----|--------|------------------|
| 1   | Mensaje de búsqueda visible antes de pulsar Search | **Cerrado.** Hecho: reset de estado al entrar en búsqueda + CSS para `[hidden]`; F1 verificado por frontend. |
| 2   | POST /api/search devuelve 503 | **Obsolete (Playwright removed).** Backend now uses only renfe_lib (GTFS + DWR). Mock `RENFE_MOCK=1` still available for testing without Renfe. |
| 3   | Búsqueda tarda y acaba en 503 | **Obsolete (Playwright removed).** Same as Bug 2; no browser timeouts. |

---

*Documento generado por el flujo de manual-qa. Actualizar este archivo en cada nueva pasada de QA.*
