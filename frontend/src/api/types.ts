export type IsoDate = string // YYYY-MM-DD
export type TimeHHMM = string // HH:MM

export interface TripListItem {
  id: number
  origin: string
  destination: string
  date: IsoDate
  departure_time?: TimeHHMM | null
  train_identifier: string
  check_interval_minutes: number
  // Latest price computed server-side from price_events (fallback handled server-side).
  // Null means the trip hasn't been published/has no price yet.
  current_price?: number | null
  // Direction of the last price change relative to the previous known price.
  // Null/undefined means unknown or no previous change.
  last_price_change_direction?: 'up' | 'down' | null
  initial_price?: number | null
  last_checked_at?: string | null
  estimated_price_min?: number | null
  estimated_price_max?: number | null
  // Present in some responses; list endpoint currently doesn't include events.
  price_events?: PriceEvent[] | null
}

export interface PriceEvent {
  id: number
  trip_id: number
  price_detected?: number | null
  detected_at: string
}

export interface ListTripsResponse {
  trips: TripListItem[]
}

export interface GetTripResponse {
  trip: TripListItem
  price_events: PriceEvent[]
}

export interface CreateTripBody {
  origin: string
  destination: string
  date: IsoDate
  train_identifier: string
  check_interval_minutes: number
  initial_price?: number | null
  departure_time?: TimeHHMM
  estimated_prices?: number[]
}

export interface SearchOptionsResponse {
  origins: string[]
  destinations: string[]
}

export interface TrainResult {
  name: string
  price?: number | null
  duration_minutes?: number | null
  estimated_price_min?: number | null
  estimated_price_max?: number | null
  estimated_prices?: number[]
  is_possible?: boolean
  inferred_from_date?: string | null
  departure_time?: TimeHHMM | null
}

export interface SearchBody {
  date: IsoDate
  origin: string
  destination: string
}

export interface SearchResponse {
  trains: TrainResult[]
}

