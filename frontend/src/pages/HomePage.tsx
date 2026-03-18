import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { deleteTrip, listTrips } from '../api/client'
import type { TripListItem } from '../api/types'

function compareIso(a: string, b: string) {
  if (a === b) return 0
  return a < b ? -1 : 1
}

function compareTrips(a: TripListItem, b: TripListItem) {
  const aHasTime = Boolean(a.departure_time)
  const bHasTime = Boolean(b.departure_time)
  if (aHasTime !== bHasTime) return aHasTime ? -1 : 1 // missing time last overall

  const d = compareIso(a.date ?? '', b.date ?? '')
  if (d !== 0) return d

  if (aHasTime && bHasTime) {
    const t = compareIso(a.departure_time as string, b.departure_time as string)
    if (t !== 0) return t
  }

  return (a.id ?? 0) - (b.id ?? 0)
}

function clamp01(n: number) {
  if (n < 0) return 0
  if (n > 1) return 1
  return n
}

function priceColor(current: number | null | undefined, min: number | null | undefined, max: number | null | undefined) {
  const c = Number(current)
  const mn = Number(min)
  const mx = Number(max)
  if (!Number.isFinite(c) || !Number.isFinite(mn) || !Number.isFinite(mx)) return undefined
  if (mx <= mn) return undefined
  const t = clamp01((c - mn) / (mx - mn)) // 0 green → 1 red
  const hue = 120 * (1 - t)
  return `hsl(${hue} 55% 32%)`
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

function formatCheckInterval(minutes?: number | null) {
  if (!minutes || minutes <= 0) return '—'
  if (minutes < 60) return `Every ${minutes} min`
  const hours = minutes / 60
  return `Every ${hours === 1 ? '1 h' : `${hours} h`}`
}

export function HomePage() {
  const [trips, setTrips] = useState<TripListItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [removeId, setRemoveId] = useState<number | null>(null)
  const [removing, setRemoving] = useState(false)

  async function refresh() {
    setError(null)
    try {
      const data = await listTrips()
      setTrips(data)
    } catch (e) {
      setTrips([])
      setError(e instanceof Error ? e.message : 'Error loading trips')
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  const groups = useMemo(() => {
    const items = trips ?? []
    const map = new Map<string, { key: string; origin: string; destination: string; trips: TripListItem[] }>()
    for (const t of items) {
      const origin = t.origin ?? ''
      const destination = t.destination ?? ''
      const key = `${origin} → ${destination}`
      const g = map.get(key) ?? { key, origin, destination, trips: [] }
      g.trips.push(t)
      map.set(key, g)
    }
    const list = Array.from(map.values())
    for (const g of list) g.trips.sort(compareTrips)
    list.sort((a, b) => compareTrips(a.trips[0], b.trips[0]))
    return list
  }, [trips])

  const empty = (trips?.length ?? 0) === 0

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">Tracked trips</h2>
        <Link
          to="/search"
          className="inline-flex items-center rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
        >
          Track new trip
        </Link>
      </div>

      {trips == null ? (
        <div className="rounded-lg bg-white p-4 shadow-sm text-sm text-gray-600">Loading trips…</div>
      ) : error ? (
        <div className="rounded-lg bg-white p-4 shadow-sm text-sm text-red-700">
          Error loading trips: {error}
        </div>
      ) : empty ? (
        <div className="rounded-lg bg-white p-6 shadow-sm text-center">
          <p className="text-sm text-gray-600">No tracked trips yet.</p>
          <div className="mt-4">
            <Link
              to="/search"
              className="inline-flex items-center rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
            >
              Track new trip
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {groups.map((g) => (
            <section key={g.key} className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-renfe-purple/20">
              <div className="bg-renfeHeader px-4 py-3 text-white">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-sm font-semibold">{g.key}</h3>
                  <span className="text-xs text-white/85">{g.trips.length} tracked</span>
                </div>
              </div>

              <ul className="divide-y divide-gray-100">
                {g.trips.map((t) => {
                  const notPublished = t.initial_price == null
                  const currentPrice = t.initial_price
                  const color = priceColor(currentPrice, t.estimated_price_min ?? null, t.estimated_price_max ?? null)
                  const dateLabel = [t.date, t.departure_time].filter(Boolean).join(' · ')

                  const rangeMin = t.estimated_price_min
                  const rangeMax = t.estimated_price_max
                  const hasMin = typeof rangeMin === 'number' && Number.isFinite(rangeMin)
                  const hasMax = typeof rangeMax === 'number' && Number.isFinite(rangeMax)
                  const fmt = (n: number) => n.toFixed(2).replace('.', ',')

                  return (
                    <li key={t.id} className="px-4 py-4">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                            <div className="text-sm font-semibold text-gray-900">{t.train_identifier}</div>
                            <div className="text-sm text-gray-600">{dateLabel}</div>
                          </div>
                          <div className="mt-1 text-xs text-gray-600">
                            <span className="font-medium text-gray-700">Check</span> {formatCheckInterval(t.check_interval_minutes)}
                          </div>
                          {(hasMin || hasMax) && (
                            <div className="mt-1 text-xs text-gray-600">
                              {hasMin && hasMax ? (
                                <>
                                  <span className="font-medium text-gray-700">Precio habitual:</span> {fmt(rangeMin!)} € – {fmt(rangeMax!)} €
                                </>
                              ) : hasMin ? (
                                <>
                                  <span className="font-medium text-gray-700">Precio habitual:</span> desde {fmt(rangeMin!)} €
                                </>
                              ) : (
                                <>
                                  <span className="font-medium text-gray-700">Precio habitual:</span> hasta {fmt(rangeMax!)} €
                                </>
                              )}
                            </div>
                          )}
                          <div className="mt-1 text-xs text-gray-500">Last checked at: {formatLastCheckedAt(t.last_checked_at)}</div>
                        </div>

                        <div className="flex flex-row items-center justify-between gap-3 sm:flex-col sm:items-end">
                          <div className="text-right">
                            {notPublished ? (
                              <div className="text-sm italic text-gray-500">Trip not yet published</div>
                            ) : (
                              <div className="text-lg font-semibold" style={color ? { color } : undefined}>
                                €{currentPrice != null ? Number(currentPrice).toFixed(2) : '—'}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-3 text-sm">
                            <Link to={`/trip/${t.id}`} className="font-medium text-renfe-red hover:text-renfe-redHover">
                              View details
                            </Link>
                            <button
                              type="button"
                              onClick={() => setRemoveId(t.id)}
                              className="rounded-md border border-gray-200 px-2.5 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </section>
          ))}
        </div>
      )}

      <Dialog open={removeId != null} onClose={() => (removing ? null : setRemoveId(null))} className="relative z-50">
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
                onClick={() => setRemoveId(null)}
                className="rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-60"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={removing || removeId == null}
                onClick={async () => {
                  if (removeId == null) return
                  setRemoving(true)
                  try {
                    await deleteTrip(removeId)
                    setRemoveId(null)
                    await refresh()
                  } catch (e) {
                    setError(e instanceof Error ? e.message : 'Could not remove trip')
                    setRemoveId(null)
                  } finally {
                    setRemoving(false)
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

