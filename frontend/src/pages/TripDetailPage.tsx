import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { deleteTrip, getTrip } from '../api/client'
import type { PriceEvent, TripListItem } from '../api/types'

function getCurrentPrice(trip: TripListItem, events: PriceEvent[]) {
  if (Array.isArray(events) && events.length > 0) {
    const latest = events.reduce((a, e) => (e.detected_at > (a?.detected_at ?? '') ? e : a), events[0])
    if (latest?.price_detected != null) return latest.price_detected
  }
  return trip.initial_price ?? null
}

function formatLastCheckedAt(iso?: string | null) {
  if (!iso) return 'Not checked yet'
  try {
    const d = new Date(iso)
    return d.toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' })
  } catch {
    return iso
  }
}

function formatDetectedAt(iso?: string | null) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString('es-ES', { dateStyle: 'short', timeStyle: 'short' })
  } catch {
    return iso
  }
}

function formatCheckInterval(minutes?: number | null) {
  if (!minutes || minutes <= 0) return '—'
  if (minutes < 60) return `Every ${minutes} min`
  const hours = minutes / 60
  return `Every ${hours === 1 ? '1 h' : `${hours} h`}`
}

export function TripDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const tripId = id ? parseInt(id, 10) : NaN

  const [trip, setTrip] = useState<TripListItem | null>(null)
  const [events, setEvents] = useState<PriceEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [removeOpen, setRemoveOpen] = useState(false)
  const [removing, setRemoving] = useState(false)

  useEffect(() => {
    if (!Number.isFinite(tripId)) {
      setLoading(false)
      setError('Trip not found')
      return
    }
    let mounted = true
    setLoading(true)
    setError(null)
    void (async () => {
      try {
        const res = await getTrip(tripId)
        if (!mounted) return
        setTrip(res.trip)
        setEvents(Array.isArray(res.price_events) ? res.price_events : [])
      } catch (e) {
        if (!mounted) return
        setError(e instanceof Error ? e.message : 'Error loading trip')
      } finally {
        if (!mounted) return
        setLoading(false)
      }
    })()
    return () => {
      mounted = false
    }
  }, [tripId])

  const currentPrice = useMemo(() => (trip ? getCurrentPrice(trip, events) : null), [trip, events])

  if (loading) {
    return <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5 text-sm text-gray-600">Loading trip…</div>
  }

  if (error || !trip) {
    return (
      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5">
        <p className="text-sm text-red-700">{error ?? 'Trip not found'}</p>
        <div className="mt-4">
          <Link to="/" className="text-sm font-medium text-renfe-red hover:text-renfe-redHover">
            ← Back to trips
          </Link>
        </div>
      </div>
    )
  }

  const notPublished = trip.initial_price == null && events.length === 0
  const meta = [
    trip.date,
    trip.departure_time ? String(trip.departure_time) : null,
    trip.train_identifier,
    `Price checked ${formatCheckInterval(trip.check_interval_minutes).replace(/^Every /, '').toLowerCase()}`,
  ]
    .filter(Boolean)
    .join(' · ')

  const fmt = (n: number) => Number(n).toFixed(2).replace('.', ',')
  const hasMin = typeof trip.estimated_price_min === 'number'
  const hasMax = typeof trip.estimated_price_max === 'number'

  return (
    <div className="space-y-4">
      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-gray-900">
              {trip.origin} → {trip.destination}
            </h2>
            <div className="mt-1 text-sm text-gray-600">{meta}</div>
          </div>
          <button
            type="button"
            onClick={() => setRemoveOpen(true)}
            className="rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
          >
            Remove trip
          </button>
        </div>

        <div className="mt-4 rounded-lg bg-gray-50 p-4 ring-1 ring-gray-100">
          {notPublished ? (
            <div className="text-sm italic text-gray-500">Trip not yet published</div>
          ) : (
            <div className="text-lg font-semibold text-renfe-purple">
              Current price: €{currentPrice != null ? Number(currentPrice).toFixed(2) : '—'}
            </div>
          )}
          {(hasMin || hasMax) && (
            <div className="mt-1 text-sm text-gray-600">
              {hasMin && hasMax ? (
                <>
                  <span className="font-medium text-gray-700">Precio habitual:</span> {fmt(trip.estimated_price_min!)} € – {fmt(trip.estimated_price_max!)} €
                </>
              ) : hasMin ? (
                <>
                  <span className="font-medium text-gray-700">Precio habitual:</span> desde {fmt(trip.estimated_price_min!)} €
                </>
              ) : (
                <>
                  <span className="font-medium text-gray-700">Precio habitual:</span> hasta {fmt(trip.estimated_price_max!)} €
                </>
              )}
            </div>
          )}
          <div className="mt-1 text-sm text-gray-600">Last checked at: {formatLastCheckedAt(trip.last_checked_at)}</div>
        </div>
      </div>

      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5">
        <h3 className="text-sm font-semibold text-gray-900">Price history</h3>
        {events.length === 0 ? (
          <p className="mt-3 text-sm text-gray-600">{notPublished ? 'No price changes yet. Trip not yet published.' : 'No price changes yet.'}</p>
        ) : (
          <ul className="mt-3 divide-y divide-gray-100">
            {events.map((ev) => (
              <li key={ev.id} className="flex items-center justify-between gap-4 py-3">
                <div className="text-sm font-semibold text-renfe-purple">€{ev.price_detected != null ? Number(ev.price_detected).toFixed(2) : '—'}</div>
                <div className="text-sm text-gray-600">{formatDetectedAt(ev.detected_at)}</div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <Dialog open={removeOpen} onClose={() => (removing ? null : setRemoveOpen(false))} className="relative z-50">
        <div className="fixed inset-0 bg-black/40" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <DialogPanel className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl ring-1 ring-black/5">
            <DialogTitle className="text-base font-semibold text-gray-900">Remove tracked trip?</DialogTitle>
            <p className="mt-2 text-sm text-gray-600">
              This will stop tracking this trip and remove it from the list. Price history will be deleted. This cannot be undone.
            </p>
            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                disabled={removing}
                onClick={() => setRemoveOpen(false)}
                className="rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-60"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={removing}
                onClick={async () => {
                  if (!Number.isFinite(tripId)) return
                  setRemoving(true)
                  try {
                    await deleteTrip(tripId)
                    navigate('/')
                  } catch (e) {
                    setError(e instanceof Error ? e.message : 'Could not remove trip')
                  } finally {
                    setRemoving(false)
                    setRemoveOpen(false)
                  }
                }}
                className="rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover disabled:opacity-60"
              >
                Remove
              </button>
            </div>
          </DialogPanel>
        </div>
      </Dialog>
    </div>
  )
}

