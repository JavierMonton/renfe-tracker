import { Combobox } from '@headlessui/react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getSearchOptions, searchTrains } from '../api/client'
import type { TrainResult } from '../api/types'

type SearchStore = {
  date: string
  origin: string
  destination: string
  trains: TrainResult[]
}

function defaultTomorrowIso() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

function StationCombobox(props: {
  label: string
  value: string
  onChange: (value: string) => void
  options: string[]
  placeholder?: string
  noMatchesText: string
}) {
  const [query, setQuery] = useState('')
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return props.options
    return props.options.filter((o) => o.toLowerCase().includes(q)).slice(0, 50)
  }, [props.options, query])

  return (
    <div className="w-full">
      <Combobox
        value={props.value}
        onChange={(v) => {
          if (typeof v === 'string') props.onChange(v)
        }}
      >
        <Combobox.Label className="block text-sm font-medium text-gray-900">{props.label}</Combobox.Label>
        <div className="relative mt-1">
          <Combobox.Input
            className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-renfe-purple focus:outline-none focus:ring-2 focus:ring-renfe-purple/30"
            displayValue={(v: string) => v}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={props.placeholder}
          />
          <Combobox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 text-sm shadow-lg focus:outline-none">
            {filtered.length === 0 ? (
              <div className="px-3 py-2 text-gray-500">{props.noMatchesText}</div>
            ) : (
              filtered.map((opt) => (
                <Combobox.Option
                  key={opt}
                  value={opt}
                  className={({ active }) =>
                    `cursor-pointer select-none px-3 py-2 ${active ? 'bg-renfe-purple/10 text-gray-900' : 'text-gray-700'}`
                  }
                >
                  {opt}
                </Combobox.Option>
              ))
            )}
          </Combobox.Options>
        </div>
      </Combobox>
    </div>
  )
}

export function SearchPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [date, setDate] = useState(defaultTomorrowIso())
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [options, setOptions] = useState<string[]>([])
  const [loadingOptions, setLoadingOptions] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    setLoadingOptions(true)
    void (async () => {
      try {
        const res = await getSearchOptions()
        if (!mounted) return
        setOptions(Array.from(new Set([...(res.origins ?? []), ...(res.destinations ?? [])])).sort())
      } catch {
        if (!mounted) return
        setOptions([])
      } finally {
        if (!mounted) return
        setLoadingOptions(false)
      }
    })()
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">{t('search.title')}</h2>
          <p className="mt-1 text-sm text-gray-600">{t('search.description')}</p>
        </div>
        <button
          type="button"
          onClick={() => {
            const o = origin
            setOrigin(destination)
            setDestination(o)
          }}
          className="rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
        >
          {t('search.swap')}
        </button>
      </div>

      <form
        className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2"
        onSubmit={async (e) => {
          e.preventDefault()
          setError(null)
          const o = origin.trim()
          const d = destination.trim()
          if (!date || !o || !d) return
          setLoading(true)
          try {
            const res = await searchTrains({ date, origin: o, destination: d })
            const payload: SearchStore = { date, origin: o, destination: d, trains: res.trains ?? [] }
            sessionStorage.setItem('renfe_search', JSON.stringify(payload))
            navigate('/results')
          } catch (err) {
            setError(err instanceof Error ? err.message : t('search.searchBtn'))
          } finally {
            setLoading(false)
          }
        }}
      >
        <div className="sm:col-span-2">
          <label className="block text-sm font-medium text-gray-900" htmlFor="search-date">
            {t('search.date')}
          </label>
          <input
            id="search-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="mt-1 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-renfe-purple focus:outline-none focus:ring-2 focus:ring-renfe-purple/30"
            required
          />
        </div>

        <StationCombobox
          label={t('search.origin')}
          value={origin}
          onChange={setOrigin}
          options={options}
          placeholder={loadingOptions ? t('search.loadingStations') : t('search.startTyping')}
          noMatchesText={t('search.noMatches')}
        />
        <StationCombobox
          label={t('search.destination')}
          value={destination}
          onChange={setDestination}
          options={options}
          placeholder={loadingOptions ? t('search.loadingStations') : t('search.startTyping')}
          noMatchesText={t('search.noMatches')}
        />

        {error && (
          <div className="sm:col-span-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">
            {error}
          </div>
        )}

        <div className="sm:col-span-2">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex w-full items-center justify-center rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
          >
            {loading ? (
              <span className="inline-flex items-center gap-2">
                <svg
                  className="h-4 w-4 animate-spin text-white"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 0 1 8-8v2.5a5.5 5.5 0 0 0-5.5 5.5H4z"
                  />
                </svg>
                {t('search.searching')}
              </span>
            ) : (
              t('search.searchBtn')
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
