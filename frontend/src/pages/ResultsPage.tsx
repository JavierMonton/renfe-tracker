import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createTrip } from '../api/client'
import type { TrainResult } from '../api/types'

type SearchStore = {
  date: string
  origin: string
  destination: string
  trains: TrainResult[]
}

const TRACK_INTERVAL_OPTIONS = [
  { value: 1, label: 'Every 1 minute' },
  { value: 5, label: 'Every 5 minutes' },
  { value: 10, label: 'Every 10 minutes' },
  { value: 30, label: 'Every 30 minutes' },
  { value: 60, label: 'Every 1 hour' },
  { value: 120, label: 'Every 2 hours' },
  { value: 360, label: 'Every 6 hours' },
  { value: 720, label: 'Every 12 hours' },
]

function formatDuration(minutes?: number | null) {
  if (!minutes || minutes <= 0) return ''
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h <= 0) return `${m} min`
  return m > 0 ? `${h} h ${m} min` : `${h} h`
}

function formatInferredDate(yyyyMmDd?: string | null) {
  if (!yyyyMmDd) return ''
  try {
    const [y, m, d] = yyyyMmDd.split('-')
    if (y && m && d) return `${d}/${m}/${y}`
  } catch {
    // ignore
  }
  return yyyyMmDd
}

export function ResultsPage() {
  const navigate = useNavigate()
  const [pending, setPending] = useState<{ train: TrainResult; interval: number } | null>(null)
  const [tracking, setTracking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const store = useMemo(() => {
    const raw = sessionStorage.getItem('renfe_search')
    if (!raw) return null
    try {
      return JSON.parse(raw) as SearchStore
    } catch {
      return null
    }
  }, [])

  if (!store) {
    return (
      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5">
        <p className="text-sm text-gray-700">No search results. Go back to search and try again.</p>
        <button
          type="button"
          onClick={() => navigate('/search')}
          className="mt-4 rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white hover:bg-renfe-redHover"
        >
          Back to search
        </button>
      </div>
    )
  }

  const trains = store.trains ?? []

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-xl shadow-sm ring-1 ring-renfe-purple/20">
        <div className="bg-renfeHeader px-4 py-3 text-white">
          <div className="flex items-center gap-3">
            <h2 className="text-base font-semibold">{store.origin} → {store.destination}</h2>
            <span className="text-xs text-white/85">{store.date}</span>
          </div>
        </div>
      </div>

      {trains.length === 0 ? (
        <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5">
          <p className="text-sm text-gray-700">No trains found for this search.</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {trains.map((t, idx) => {
            const duration = formatDuration(t.duration_minutes)
            const depTime = t.departure_time ? String(t.departure_time) : ''

            const fmt = (n: number) => Number(n).toFixed(2).replace('.', ',')
            const hasMin = typeof t.estimated_price_min === 'number'
            const hasMax = typeof t.estimated_price_max === 'number'

            return (
              <li
                key={`${t.name}-${idx}-${depTime}`}
                className={`rounded-xl border p-4 shadow-sm ${
                  t.is_possible ? 'border-dashed border-gray-300 bg-gray-100' : 'border-gray-200 bg-white'
                }`}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                      <div className="text-sm font-semibold text-gray-900">{t.name || 'Train'}</div>
                      {(depTime || duration) && (
                        <div className="text-sm text-gray-600">
                          {[depTime ? `Salida: ${depTime}` : null, duration ? `Duración: ${duration}` : null]
                            .filter(Boolean)
                            .join(' · ')}
                        </div>
                      )}
                    </div>

                    {(hasMin || hasMax) && (
                      <div className="mt-1.5 text-sm text-gray-600">
                        <span className="font-medium text-gray-700">Precio habitual: </span>
                        {hasMin && hasMax ? (
                          <>
                            <span className="font-semibold text-green-700">{fmt(t.estimated_price_min!)} €</span>
                            {' – '}
                            <span className="font-semibold text-red-700">{fmt(t.estimated_price_max!)} €</span>
                          </>
                        ) : hasMin ? (
                          <>desde <span className="font-semibold text-green-700">{fmt(t.estimated_price_min!)} €</span></>
                        ) : (
                          <>hasta <span className="font-semibold text-red-700">{fmt(t.estimated_price_max!)} €</span></>
                        )}
                      </div>
                    )}

                    {t.is_possible && (
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <span className="inline-flex items-center rounded-md border border-gray-300 bg-white px-2 py-1 text-xs font-medium text-gray-700">
                          Tren posible – aún no publicado para esta fecha
                        </span>
                        {t.inferred_from_date && (
                          <span className="text-xs text-gray-500">Inferido desde {formatInferredDate(t.inferred_from_date)}</span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between gap-4 sm:flex-col sm:items-end">
                    <div className="text-right">
                      <div className="text-lg font-semibold text-renfe-purple">
                        €{t.price != null ? Number(t.price).toFixed(2) : '—'}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setPending({ train: t, interval: 60 })}
                      className="inline-flex items-center justify-center rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
                    >
                      Track this trip
                    </button>
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      )}

      <Dialog open={pending != null} onClose={() => (tracking ? null : setPending(null))} className="relative z-50">
        <div className="fixed inset-0 bg-black/40" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <DialogPanel className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl ring-1 ring-black/5">
            <DialogTitle className="text-base font-semibold text-gray-900">How often to track?</DialogTitle>
            <p className="mt-2 text-sm text-gray-600">We will check the price at this interval.</p>

            {error && <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">{error}</div>}

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-900" htmlFor="track-interval">
                Check interval
              </label>
              <select
                id="track-interval"
                value={pending?.interval ?? 60}
                onChange={(e) => setPending((p) => (p ? { ...p, interval: parseInt(e.target.value, 10) } : p))}
                className="mt-1 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-renfe-purple focus:outline-none focus:ring-2 focus:ring-renfe-purple/30"
              >
                {TRACK_INTERVAL_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                disabled={tracking}
                onClick={() => setPending(null)}
                className="rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-60"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={tracking || pending == null}
                onClick={async () => {
                  if (!pending) return
                  setError(null)
                  setTracking(true)
                  try {
                    const train = pending.train
                    let estimated_prices: number[] = Array.isArray(train.estimated_prices) ? train.estimated_prices : []
                    if (
                      estimated_prices.length === 0 &&
                      typeof train.estimated_price_min === 'number' &&
                      typeof train.estimated_price_max === 'number'
                    ) {
                      estimated_prices = [train.estimated_price_min, train.estimated_price_max]
                    }
                    await createTrip({
                      origin: store.origin,
                      destination: store.destination,
                      date: store.date,
                      train_identifier: train.name ?? '',
                      check_interval_minutes: pending.interval,
                      initial_price: train.price != null ? Number(train.price) : null,
                      ...(train.departure_time ? { departure_time: String(train.departure_time) } : {}),
                      estimated_prices,
                    })
                    setPending(null)
                    navigate('/')
                  } catch (e) {
                    setError(e instanceof Error ? e.message : 'Could not track trip')
                  } finally {
                    setTracking(false)
                  }
                }}
                className="rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover disabled:opacity-60"
              >
                Track
              </button>
            </div>
          </DialogPanel>
        </div>
      </Dialog>
    </div>
  )
}

