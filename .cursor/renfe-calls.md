# Llamadas a la web oficial de Renfe

Este documento describe cómo realizar búsquedas de trenes contra venta.renfe.com usando el mínimo de parámetros necesario. El flujo requiere **dos pasos**: obtener sesión (cookies) y luego llamar al endpoint DWR de búsqueda.

---

## Análisis del curl original

- **Endpoint:** `https://venta.renfe.com/vol/dwr/call/plaincall/trainEnlacesManager.getTrainsList.dwr` (DWR = Direct Web Remoting, RPC estilo Java).
- **Método:** POST.
- **Cabeceras eliminadas como prescindibles:** `x-dtpc`, `tracestate`, `traceparent`, `Sec-Fetch-*`, `Priority`, `Accept-Encoding` (el servidor acepta sin compresión), `Connection`. Las cookies de tracking/analytics (Optanon, Adobe, QuantumMetric, QueueIT, dtCookie, rxVisitor, etc.) no se envían en el curl mínimo; solo se mantienen las necesarias para sesión.
- **Cabeceras mínimas necesarias:** `User-Agent`, `Content-Type: text/plain`, `Origin`, `Referer`, `Cookie` (solo las de sesión: ver abajo).
- **Cuerpo (DWR):** Se mantiene la estructura mínima. Los parámetros que **hay que sustituir** según la búsqueda son:
  - **Fecha de salida:** `c0-e8=string:DD%2FMM%2FYYYY` (ej. 01/04/2026 → `01%2F04%2F2026`).
  - **Origen (código estación):** `c0-e17=string:ORIGIN_CODE` (ej. Barcelona-Sants = `71801`).
  - **Destino (código estación):** `c0-e18=string:DEST_CODE` (ej. Calatayud = `70600`).

El resto de campos del body (tipo franja, adultos, ida/vuelta, etc.) se dejan como en el ejemplo para una búsqueda de ida simple.

---

## Paso 1: Obtener cookies de sesión

Hacer un GET a la página de búsqueda de Renfe. El servidor devuelve `Set-Cookie` con al menos `JSESSIONID` y `DWRSESSIONID`. Esas cookies son necesarias para el paso 2.

```bash
curl -s -D - -o /dev/null 'https://venta.renfe.com/vol/buscarTrenEnlaces.do' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
```

Guardar las cookies de la respuesta (cabeceras `Set-Cookie`). Para usar en el siguiente paso, concatenar en un único header `Cookie:` (o usar `-b cookies.txt` si se guardaron en archivo). Las cookies críticas son **JSESSIONID** y **DWRSESSIONID**. El valor de `scriptSessionId` del body DWR suele ser el valor de `DWRSESSIONID` + `/` + un sufijo; el sufijo puede aparecer en el HTML/JS de la página o probarse reutilizando el mismo formato en llamadas sucesivas.

---

## Paso 2: Búsqueda mínima (getTrainsList)

Sustituir en el cuerpo:

- `DATE` → fecha de ida en formato `DD%2FMM%2FYYYY` (ej. `01%2F04%2F2026`).
- `ORIGIN_CODE` → código de estación origen (ej. `71801` para Barcelona-Sants).
- `DEST_CODE` → código de estación destino (ej. `70600` para Calatayud).
- `COOKIE_HEADER` → la cadena de cookies obtenida en el paso 1 (al menos JSESSIONID y DWRSESSIONID).
- `SCRIPT_SESSION_ID` → normalmente `DWRSESSIONID` + `/` + sufijo; si no se tiene sufijo, probar solo el valor de DWRSESSIONID o extraerlo de la página del paso 1.

Curl mínimo:

```bash
curl 'https://venta.renfe.com/vol/dwr/call/plaincall/trainEnlacesManager.getTrainsList.dwr' \
  -X POST \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' \
  -H 'Content-Type: text/plain' \
  -H 'Origin: https://venta.renfe.com' \
  -H 'Referer: https://venta.renfe.com/vol/buscarTrenEnlaces.do' \
  -H 'Cookie: COOKIE_HEADER' \
  --data-raw 'callCount=1
windowName=
c0-scriptName=trainEnlacesManager
c0-methodName=getTrainsList
c0-id=0
c0-e1=string:false
c0-e2=string:false
c0-e3=string:false
c0-e4=string:S
c0-e5=string:S
c0-e6=string:00%3A00
c0-e7=string:00%3A00
c0-e8=string:DATE
c0-e9=string:
c0-e10=string:1
c0-e11=string:0
c0-e12=string:0
c0-e13=string:I
c0-e14=string:
c0-e15=string:false
c0-e16=string:false
c0-e17=string:ORIGIN_CODE
c0-e18=string:DEST_CODE
c0-e19=string:
c0-param0=Object_Object:{atendo:reference:c0-e1, sinEnlace:reference:c0-e2, plazaH:reference:c0-e3, tipoFranjaI:reference:c0-e4, tipoFranjaV:reference:c0-e5, horaFranjaIda:reference:c0-e6, horaFranjaVuelta:reference:c0-e7, fechaSalida:reference:c0-e8, fechaVuelta:reference:c0-e9, adultos:reference:c0-e10, ninos:reference:c0-e11, ninosMenores:reference:c0-e12, trayecto:reference:c0-e13, idaVuelta:reference:c0-e14, conMascota:reference:c0-e15, conBicicleta:reference:c0-e16, origen:reference:c0-e17, destino:reference:c0-e18, codPromo:reference:c0-e19}
batchId=8
instanceId=0
page=%2Fvol%2FbuscarTrenEnlaces.do
scriptSessionId=SCRIPT_SESSION_ID
'
```

La respuesta es texto DWR (no JSON); contiene los datos de trenes embebidos en el payload DWR. Para usar en Renfe Tracker hay que parsear ese texto (p. ej. extraer bloques de trenes y precios).

---

## Códigos de estación (ejemplos)

| Estación           | Código  |
|--------------------|---------|
| Barcelona-Sants    | 71801   |
| Calatayud          | 70600   |
| Madrid-Puerta de Atocha | 71800 (comprobar en la web) |
| Zaragoza-Delicias  | 78400 (comprobar en la web) |

La lista completa de códigos puede obtenerse de la propia web (HTML/JS de la página de búsqueda o de respuestas DWR). Para Renfe Tracker conviene mantener un mapa ciudad/nombre → código en el backend.

---

## Resumen

- **Dos llamadas:** (1) GET a `buscarTrenEnlaces.do` para obtener cookies; (2) POST al DWR `trainEnlacesManager.getTrainsList.dwr` con fecha, origen y destino en el body.
- **Sustituir en el body:** `c0-e8` (fecha), `c0-e17` (origen), `c0-e18` (destino), y en la cabecera Cookie y en scriptSessionId los valores de sesión del paso 1.
- **Cookies:** Necesarias; sin ellas el DWR suele devolver error o redirección. Basta con obtenerlas desde la página oficial de búsqueda.


# Posible manera de obtener una cookie
Este curl es el primero que se ejecuta en Renfe cuando un usuario entra con un navegador. 

curl 'https://cdn.cookielaw.org/consent/fda0de57-6fc5-40a5-b2fa-56b1dc315fdd/fda0de57-6fc5-40a5-b2fa-56b1dc315fdd.json' \
  --compressed \
  -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0' \
  -H 'Accept: */*' \
  -H 'Accept-Language: en-US,es-ES;q=0.9,es;q=0.8,en;q=0.7' \
  -H 'Accept-Encoding: gzip, deflate, br, zstd' \
  -H 'Origin: https://www.renfe.com' \
  -H 'Connection: keep-alive' \
  -H 'Referer: https://www.renfe.com/' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: cross-site'

  Es posible que se use para obtener una cookie que luego se use en el resto de peticiones.