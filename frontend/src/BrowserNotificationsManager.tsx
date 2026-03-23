import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { getTrip, listNotifications, listTrips } from './api/client'
import type { NotificationListItem, PriceEvent, TripListItem } from './api/types'

function formatPrice(p: number | null | undefined): string {
  if (p == null) return 'N/A'
  if (!Number.isFinite(p)) return 'N/A'
  return p.toFixed(2)
}

function buildPriceChangeSummary(t: TFunction, trip: TripListItem, oldPrice: number | null, newPrice: number | null, departureTime?: string | null) {
  const dep = departureTime ?? 'N/A'
  return t('browserNotif.body', {
    origin: trip.origin,
    destination: trip.destination,
    departure: dep,
    oldPrice: formatPrice(oldPrice),
    newPrice: formatPrice(newPrice),
  })
}

export function BrowserNotificationsManager() {
  const { t } = useTranslation()
  const [browserEnabled, setBrowserEnabled] = useState(false)

  // tripId -> last_price_changed_at we have already handled
  const seenRef = useRef<Record<number, string | null>>({})
  const mountedRef = useRef(false)

  useEffect(() => {
    let cancelled = false
    mountedRef.current = true

    void (async () => {
      try {
        const notifs: NotificationListItem[] = await listNotifications()
        if (cancelled) return
        const enabled = notifs.some((n) => n.type === 'browser')
        setBrowserEnabled(enabled)

        // Prime the map so we only notify on subsequent changes.
        const trips = await listTrips()
        if (cancelled) return
        const nextSeen: Record<number, string | null> = {}
        for (const tr of trips) {
          nextSeen[tr.id] = tr.last_price_changed_at ?? null
        }
        seenRef.current = nextSeen
      } catch {
        // Ignore: notifications are best-effort.
      }
    })()

    return () => {
      cancelled = true
      mountedRef.current = false
    }
  }, [])

  useEffect(() => {
    const tick = async () => {
      if (!browserEnabled) return
      if (typeof Notification === 'undefined') return
      if (Notification.permission !== 'granted') return

      try {
        const trips = await listTrips()
        for (const tr of trips) {
          const currentChangedAt = tr.last_price_changed_at ?? null
          const prevChangedAt = seenRef.current[tr.id] ?? null

          if (!currentChangedAt) continue
          if (prevChangedAt === currentChangedAt) continue

          // Update immediately to avoid duplicate notifications if getTrip is slow.
          seenRef.current[tr.id] = currentChangedAt

          const res = await getTrip(tr.id)
          const trip = res.trip
          const events: PriceEvent[] = Array.isArray(res.price_events) ? (res.price_events as PriceEvent[]) : []

          const newPrice = typeof events[0]?.price_detected === 'number' ? (events[0].price_detected as number) : null
          const oldPrice = typeof events[1]?.price_detected === 'number' ? (events[1].price_detected as number) : null

          const summary = buildPriceChangeSummary(
            t,
            trip,
            oldPrice,
            newPrice,
            trip.departure_time ?? null,
          )

          if (Notification.permission === 'granted') {
            // eslint-disable-next-line no-new
            new Notification(t('browserNotif.title'), { body: summary })
          }
        }
      } catch {
        // Ignore: best-effort.
      }
    }

    const interval = window.setInterval(() => {
      void tick()
    }, 60_000)

    return () => {
      window.clearInterval(interval)
    }
  }, [browserEnabled])

  return null
}

