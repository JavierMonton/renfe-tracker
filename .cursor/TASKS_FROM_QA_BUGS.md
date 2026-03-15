# Tareas derivadas de bugs-found-by-qa.md

El manager-architect asigna estas tareas a los subagentes para corregir los bugs reportados por QA. Origen: `bugs-found-by-qa.md`.

---

## Tarea F1 (Frontend) – Bug 1: Mensaje de carga antes de Search

**Asignado a:** frontend-web-developer

**Objetivo:** Asegurar que el mensaje "Consultando Renfe…" y el spinner **no** se muestren hasta que el usuario pulse "Search".

**Criterios de aceptación:**
- Al entrar en la vista de búsqueda (Track new trip), solo se ve el formulario y el botón "Search". No debe verse el bloque de carga.
- El bloque de carga solo aparece después de pulsar Search y debe ocultarse al terminar la petición (éxito o error).
- Si el usuario vuelve a la búsqueda tras una petición anterior, el botón debe estar habilitado y con texto "Search", y el bloque de carga oculto.

**Archivos relevantes:** `app/static/js/app.js`, `app/static/index.html`, `app/static/css/style.css`

**Nota:** En una pasada anterior se añadió reset de estado en `loadSearch()` y `.search-loading[hidden] { display: none !important; }`. Verificar que está aplicado y que no hay regresiones (p. ej. el bloque visible por defecto en algún navegador).

---

## Tarea B1 (Backend) – Bugs 2 y 3: 503 en búsqueda y modo sin Chromium

**Asignado a:** backend-developer

**Objetivo:** Que la búsqueda sea usable cuando Chromium no está disponible (p. ej. desarrollo local) y que los errores 503 sean más claros.

**Criterios de aceptación:**

1. **Modo mock con variable de entorno**
   - Si existe la variable de entorno `RENFE_MOCK=1` (o `RENFE_USE_MOCK=true`), el endpoint `POST /api/search` **no** debe llamar a Playwright ni a la web de Renfe. Debe devolver una lista fija de trenes de ejemplo (p. ej. 2–3 trenes con nombre, precio, duración) para la fecha/origen/destino que envíe el frontend.
   - Así el frontend y el flujo se pueden probar sin instalar Chromium. En Docker o producción, no se define `RENFE_MOCK` y se usa el cliente real.

2. **Mensajes de error 503 más claros**
   - Cuando el cliente Renfe falle, el `detail` de la respuesta 503 debe distinguir cuando sea posible:
     - Chromium no instalado (p. ej. "Renfe no disponible: navegador no instalado. Ejecuta 'playwright install chromium' o usa Docker.").
     - Timeout ("Renfe tardó demasiado en responder.").
     - Otro error (mensaje genérico o el que devuelva la excepción).
   - No cambiar la lógica de negocio; solo mejorar el texto que se devuelve al frontend.

3. **Documentación**
   - En el README (o en este documento) dejar indicado que para búsqueda real hace falta Docker o `playwright install chromium`, y que con `RENFE_MOCK=1` se pueden probar búsquedas sin Renfe.

**Archivos relevantes:** `app/renfe_client.py`, `app/api/search.py`, `README.md`

**Referencia:** Ver causas raíz en `bugs-found-by-qa.md` (Bug 2 y Bug 3).

---

## Resumen de asignaciones

| Tarea | Subagente              | Bug(s) | Resumen                                              |
|-------|------------------------|--------|------------------------------------------------------|
| F1    | frontend-web-developer | 1      | Verificar/corregir que el mensaje de carga no se vea antes de Search. |
| B1    | backend-developer      | 2, 3   | Modo mock (RENFE_MOCK), mensajes 503 más claros, documentar. |

---

## Estado de ejecución

- **F1:** Completada por frontend-web-developer. Comportamiento ya cumplía criterios; se añadieron comentarios (F1) en HTML y CSS.
- **B1:** Completada por backend-developer. Modo mock (`RENFE_MOCK=1`), subclases de error (navegador no instalado, timeout), mensajes 503 claros y nota en README.
