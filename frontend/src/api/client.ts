import type {
  CreateTripBody,
  GetTripResponse,
  ListTripsResponse,
  SearchBody,
  SearchOptionsResponse,
  SearchResponse,
  CreateNotificationBody,
  CreateNotificationResponse,
  ListNotificationsResponse,
  NotificationConfigStatus,
  NotificationListItem,
  TripListItem,
} from './types'

const API_BASE = '/api'

async function readJson<T>(res: Response): Promise<T> {
  const text = await res.text()
  if (!text) return {} as T
  try {
    return JSON.parse(text) as T
  } catch {
    throw new Error('Invalid JSON response')
  }
}

function extractErrorMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') return null
  const anyPayload = payload as any
  if (typeof anyPayload.detail === 'string') return anyPayload.detail
  if (typeof anyPayload.message === 'string') return anyPayload.message
  return null
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API_BASE + path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  })

  if (res.ok) {
    // 204 has no body
    if (res.status === 204) return undefined as T
    return await readJson<T>(res)
  }

  let payload: unknown = null
  try {
    payload = await readJson<unknown>(res)
  } catch {
    // ignore
  }

  const msg = extractErrorMessage(payload) ?? res.statusText ?? 'Request failed'
  throw new Error(msg)
}

export async function listTrips(): Promise<TripListItem[]> {
  const data = await apiFetch<ListTripsResponse>('/trips')
  return Array.isArray(data.trips) ? data.trips : []
}

export async function createTrip(body: CreateTripBody): Promise<TripListItem> {
  return await apiFetch<TripListItem>('/trips', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getTrip(tripId: number | string): Promise<GetTripResponse> {
  return await apiFetch<GetTripResponse>(`/trips/${tripId}`)
}

export async function deleteTrip(tripId: number | string): Promise<void> {
  await apiFetch<void>(`/trips/${tripId}`, { method: 'DELETE' })
}

export async function getSearchOptions(): Promise<SearchOptionsResponse> {
  return await apiFetch<SearchOptionsResponse>('/search/options', { method: 'GET' })
}

export async function searchTrains(body: SearchBody): Promise<SearchResponse> {
  return await apiFetch<SearchResponse>('/search', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getNotificationConfigStatus(): Promise<NotificationConfigStatus> {
  return await apiFetch<NotificationConfigStatus>('/notifications/config-status', { method: 'GET' })
}

export async function listNotifications(): Promise<NotificationListItem[]> {
  const data = await apiFetch<ListNotificationsResponse>('/notifications', { method: 'GET' })
  return Array.isArray(data.notifications) ? data.notifications : []
}

export async function createNotification(body: CreateNotificationBody): Promise<CreateNotificationResponse> {
  return await apiFetch<CreateNotificationResponse>('/notifications', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function deleteNotification(notificationId: number | string): Promise<void> {
  await apiFetch<void>(`/notifications/${notificationId}`, { method: 'DELETE' })
}

