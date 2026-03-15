# Tareas: UX de búsqueda y tiempo de espera Renfe

Asignadas por el manager-architect. Objetivo: que el usuario sepa que la búsqueda está en curso y que puede tardar; evitar timeouts habituales.

---

## Tarea 1: Indicador de carga y botón deshabilitado (Frontend)

**Responsable:** frontend-web-developer (o quien mantenga la UI).

**Problema:** Tras pulsar "Search" no hay feedback: no se sabe que hay una petición en curso. El botón sigue activo y se puede enviar de nuevo el formulario.

**Criterios de aceptación:**
- Mostrar un **indicador de carga** visible mientras la petición POST /api/search está en curso (spinner, texto "Buscando…", o ambos).
- **Desactivar el botón de búsqueda** mientras la petición está en curso (y opcionalmente mostrar texto tipo "Buscando…" en el botón).
- Al terminar (éxito o error), ocultar el indicador y volver a habilitar el botón.

**Implementación sugerida:** En el `onsubmit` del formulario de búsqueda: antes del `fetch`, mostrar un bloque/span con mensaje de carga y `submitButton.disabled = true`; en el `finally` del try/catch, ocultar el mensaje y `submitButton.disabled = false`.

---

## Tarea 2: Más tiempo de espera y mensaje de duración (Backend + Frontend)

**Problema:** Aparece a menudo el mensaje de que Renfe tarda demasiado. La búsqueda en Renfe son varias consultas (cargar página, rellenar formulario, enviar, cargar resultados) y puede tardar 1–3 minutos.

**Backend (renfe_client.py):**
- Aumentar el tiempo máximo de espera (p. ej. de 45 s a **2–3 minutos**). Por ejemplo: `PAGE_TIMEOUT_MS = 180_000` y aumentar también el timeout del `wait_for_selector` de resultados si es necesario.
- No cambiar la lógica de errores; solo permitir más tiempo antes de considerar timeout.

**Frontend (mensaje al usuario):**
- Mostrar un mensaje claro mientras se busca, por ejemplo: **"Consultando Renfe… La búsqueda puede tardar 1–2 minutos."** (o barra de progreso / mensajes por fases si más adelante se añade progreso por pasos). Por ahora basta un mensaje fijo que indique que puede tardar.

**Criterios de aceptación:**
- El backend no hace timeout antes de 2–3 minutos en operaciones normales de Renfe.
- El usuario ve un mensaje que indica que la búsqueda puede tardar 1–2 minutos (junto al indicador de carga de la Tarea 1).

---

## Resumen

| Tarea | Componente        | Acción |
|-------|-------------------|--------|
| 1     | Frontend (app.js, opcional HTML/CSS) | Indicador de carga visible; botón deshabilitado mientras hay petición; mensaje tipo "Buscando… / puede tardar 1–2 min". |
| 2     | Backend (renfe_client.py) | Aumentar `PAGE_TIMEOUT_MS` (y timeouts de espera a resultados) a 2–3 minutos. |
| 2     | Frontend           | Incluir en el mensaje de carga que la búsqueda puede tardar 1–2 minutos. |

---

## Estado

- **Tarea 1:** Hecho. Indicador de carga (spinner + texto "Consultando Renfe… La búsqueda puede tardar 1-2 minutos."), botón deshabilitado y texto "Buscando…" durante la petición; se restaura en `finally`.
- **Tarea 2:** Hecho. `PAGE_TIMEOUT_MS = 180_000` (3 min) y timeout de resultados 90 s en `renfe_client.py`; mensaje de duración en el propio indicador de carga.
