---
id: notifications
sidebar_position: 4
title: Notificacions
---

# Notificacions

Quan el preu d'un viatge seguit canvia, Renfe Tracker pot notificar-te immediatament. S'admeten tres sistemes de notificació i pots configurar-ne tants com vulguis — totes les notificacions actives s'envien en cada canvi de preu.

## Format del missatge de notificació

Cada notificació (independentment del tipus) conté:

```
Trip - {origen} → {destinació}, {hora_sortida}, changed price from {preu_anterior} to {preu_nou}
```

Per exemple:

> Trip - MADRID → BARCELONA, 07:00, changed price from €45.10 to €39.50

---

## Correu electrònic {#email}

Envia un correu electrònic per SMTP cada vegada que canvia un preu.

### Configuració del servidor (variables d'entorn)

Configura la connexió al servidor SMTP en iniciar el contenidor:

```yaml
environment:
  SMTP_HOST: smtp.gmail.com
  SMTP_PORT: 587
  SMTP_USERNAME: alerts@example.com
  SMTP_PASSWORD: your-app-password
  SMTP_USE_STARTTLS: "true"
  SMTP_FROM: alerts@example.com   # opcional, per defecte usa SMTP_USERNAME
```

### Configuració per notificació (interfície)

Després de configurar la connexió al servidor, ves a **Notificacions → Afegir notificació → Email** i omple:

- **Adreça del destinatari** — on s'enviaran les alertes.
- **Assumpte** — línia d'assumpte del correu (pots incloure el que vulguis).

### Consell per a Gmail

Si uses Gmail, genera una **Contrasenya d'aplicació** (no la teva contrasenya habitual) a la configuració de seguretat del teu compte de Google i usa-la com a `SMTP_PASSWORD`. Assegura't de tenir la verificació en dos passos activada al compte.

---

## Home Assistant {#home-assistant}

Publica una notificació a un servei de notificació de Home Assistant cada vegada que canvia un preu.

### Configuració del servidor (variables d'entorn)

```yaml
environment:
  HA_URL: http://homeassistant.local:8123
  HA_TOKEN: your-long-lived-access-token
```

Genera el token a Home Assistant: **Perfil → Tokens d'accés de llarga durada → Crear token**.

### Configuració per notificació (interfície)

Ves a **Notificacions → Afegir notificació → Home Assistant** i introdueix:

- **Nom del servei** — el servei de notificació de HA a cridar, p. ex. `mobile_app_my_phone` o `notify`.

L'aplicació crida `POST /api/services/notify/{service}` a la teva instància de HA amb el missatge de canvi de preu al cos.

### Automatitzacions

Un cop la notificació arriba a Home Assistant, pots adjuntar-hi qualsevol automatització de HA — enviar-la a un bot de Telegram, fer parpellejar un llum, activar un script, etc.

---

## Notificacions del navegador {#browser}

Envia notificacions al navegador a través de l'API Web Push per rebre alertes fins i tot quan la pestanya de Renfe Tracker no està oberta (sempre que el navegador estigui en execució).

### Com funciona

El sistema de notificacions del navegador funciona de manera diferent dels altres dos:

- Un script en segon pla (`BrowserNotificationsManager`) s'executa al navegador i consulta l'API `/trips` cada 60 segons.
- Quan detecta un nou esdeveniment de preu des de l'última comprovació, dispara una notificació del navegador usant la [API de Notificacions](https://developer.mozilla.org/ca/docs/Web/API/Notifications_API).

### Configuració

1. Ves a **Notificacions → Afegir notificació → Navegador**.
2. Fes clic a **Activar notificacions del navegador** — el navegador demanarà permís.
3. Concedeix el permís.

Fet. Les notificacions apareixeran com a alertes a nivell del sistema operatiu des del teu navegador.

:::note
Les notificacions del navegador requereixen que la pestanya de Renfe Tracker hagi estat oberta almenys una vegada a la sessió del navegador perquè el script de sondeig pugui iniciar-se. Les notificacions es lliuren mentre el navegador estigui en execució; no sobreviuen a un reinici del navegador sense tornar a obrir la pestanya.
:::

---

## Gestionar notificacions

Ves a **Notificacions** a la navegació superior per veure tots els canals de notificació configurats. Pots eliminar-ne qualsevol des d'allà. Afegir-ne una de nova usa el mateix flux d'**Afegir notificació** descrit anteriorment.

Tots els enviaments de notificacions són de **millor esforç**: si el lliurament falla (error SMTP, HA no disponible, etc.) l'error es registra però el treball del planificador continua normalment — una notificació fallida mai atura la comprovació de preus.
