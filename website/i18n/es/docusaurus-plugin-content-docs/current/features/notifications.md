---
id: notifications
sidebar_position: 4
title: Notificaciones
---

# Notificaciones

Cuando el precio de un viaje seguido cambia, Renfe Tracker puede notificarte de inmediato. Se admiten tres sistemas de notificación y puedes configurar tantos como quieras — todas las notificaciones activas se disparan en cada cambio de precio.

## Formato del mensaje de notificación

Cada notificación (independientemente del tipo) contiene:

```
Trip - {origen} → {destino}, {hora_salida}, changed price from {precio_anterior} to {precio_nuevo}
```

Por ejemplo:

> Trip - MADRID → BARCELONA, 07:00, changed price from €45.10 to €39.50

---

## Correo electrónico {#email}

Envía un correo electrónico por SMTP cada vez que cambia un precio.

### Configuración del servidor (variables de entorno)

Configura la conexión al servidor SMTP al iniciar el contenedor:

```yaml
environment:
  SMTP_HOST: smtp.gmail.com
  SMTP_PORT: 587
  SMTP_USERNAME: alerts@example.com
  SMTP_PASSWORD: your-app-password
  SMTP_USE_STARTTLS: "true"
  SMTP_FROM: alerts@example.com   # opcional, por defecto usa SMTP_USERNAME
```

### Configuración por notificación (interfaz)

Después de configurar la conexión al servidor, ve a **Notificaciones → Añadir notificación → Email** y rellena:

- **Dirección del destinatario** — donde se enviarán las alertas.
- **Asunto** — línea de asunto del correo (puedes incluir lo que quieras).

### Consejo para Gmail

Si usas Gmail, genera una **Contraseña de aplicación** (no tu contraseña normal) en la configuración de seguridad de tu cuenta de Google y úsala como `SMTP_PASSWORD`. Asegúrate de tener la verificación en dos pasos activada en la cuenta.

---

## Home Assistant {#home-assistant}

Publica una notificación en un servicio de notificación de Home Assistant cada vez que cambia un precio.

### Configuración del servidor (variables de entorno)

```yaml
environment:
  HA_URL: http://homeassistant.local:8123
  HA_TOKEN: your-long-lived-access-token
```

Genera el token en Home Assistant: **Perfil → Tokens de acceso de larga duración → Crear token**.

### Configuración por notificación (interfaz)

Ve a **Notificaciones → Añadir notificación → Home Assistant** e introduce:

- **Nombre del servicio** — el servicio de notificación de HA a llamar, p. ej. `mobile_app_my_phone` o `notify`.

La aplicación llama a `POST /api/services/notify/{service}` en tu instancia de HA con el mensaje de cambio de precio en el cuerpo.

### Automatizaciones

Una vez que la notificación llega a Home Assistant, puedes adjuntarle cualquier automatización de HA — enviarla a un bot de Telegram, hacer parpadear una luz, activar un script, etc.

---

## Notificaciones del navegador {#browser}

Envía notificaciones en el navegador a través de la API Web Push para recibir alertas incluso cuando la pestaña de Renfe Tracker no está abierta (siempre que el navegador esté en ejecución).

### Cómo funciona

El sistema de notificaciones del navegador funciona de manera diferente a los otros dos:

- Un script en segundo plano (`BrowserNotificationsManager`) se ejecuta en el navegador y consulta la API `/trips` cada 60 segundos.
- Cuando detecta un nuevo evento de precio desde la última comprobación, dispara una notificación del navegador usando la [API de Notificaciones](https://developer.mozilla.org/es/docs/Web/API/Notifications_API).

### Configuración

1. Ve a **Notificaciones → Añadir notificación → Navegador**.
2. Haz clic en **Activar notificaciones del navegador** — el navegador pedirá permiso.
3. Concede el permiso.

Listo. Las notificaciones aparecerán como alertas a nivel del sistema operativo desde tu navegador.

:::note
Las notificaciones del navegador requieren que la pestaña de Renfe Tracker haya sido abierta al menos una vez en la sesión del navegador para que el script de sondeo pueda iniciarse. Las notificaciones se entregan mientras el navegador esté en ejecución; no sobreviven a un reinicio del navegador sin volver a abrir la pestaña.
:::

---

## Gestionar notificaciones

Ve a **Notificaciones** en la navegación superior para ver todos los canales de notificación configurados. Puedes eliminar cualquiera de ellos desde allí. Añadir una nueva usa el mismo flujo de **Añadir notificación** descrito anteriormente.

Todos los envíos de notificaciones son de **mejor esfuerzo**: si la entrega falla (error SMTP, HA no disponible, etc.) el error se registra pero el trabajo del planificador continúa normalmente — una notificación fallida nunca detiene la comprobación de precios.
