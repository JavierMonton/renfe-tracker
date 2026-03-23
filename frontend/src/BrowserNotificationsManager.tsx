import { useEffect, useRef, useState } from 'react'
import { getTrip, listNotifications, listTrips } from './api/client'
import type { NotificationListItem, PriceEvent, TripListItem } from './api/types'

function formatPrice(p: number | null | undefined): string {
  if (p == null) return 'N/A'
  if (!Number.isFinite(p)) return 'N/A'
  return p.toFixed(2)
}

function buildPriceChangeSummary(trip: TripListItem, oldPrice: number | null, newPrice: number | null, departureTime?: string | null) {
  const dep = departureTime ? departureTime : 'N/A'
  return `Trip - ${trip.origin} -> ${trip.destination}, ${dep}, changed price from ${formatPrice(oldPrice)} to ${formatPrice(newPrice)}`
}

export function BrowserNotificationsManager() {
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
        for (const t of trips) {
          nextSeen[t.id] = t.last_price_changed_at ?? null
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
        for (const t of trips) {
          const currentChangedAt = t.last_price_changed_at ?? null
          const prevChangedAt = seenRef.current[t.id] ?? null

          if (!currentChangedAt) continue
          if (prevChangedAt === currentChangedAt) continue

          // Update immediately to avoid duplicate notifications if getTrip is slow.
          seenRef.current[t.id] = currentChangedAt

          const res = await getTrip(t.id)
          const trip = res.trip
          const events: PriceEvent[] = Array.isArray(res.price_events) ? (res.price_events as PriceEvent[]) : []

          const newPrice = typeof events[0]?.price_detected === 'number' ? (events[0].price_detected as number) : null
          const oldPrice = typeof events[1]?.price_detected === 'number' ? (events[1].price_detected as number) : null

          const summary = buildPriceChangeSummary(
            trip,
            oldPrice,
            newPrice,
            trip.departure_time ?? null,
          )

          if (Notification.permission === 'granted') {
            // eslint-disable-next-line no-new
            new Notification('Renfe Tracker', { body: summary })
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

