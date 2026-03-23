import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { deleteNotification, getNotificationConfigStatus, listNotifications } from '../api/client'
import type { NotificationConfigStatus, NotificationListItem } from '../api/types'

function NotificationIcon({ type }: { type: NotificationListItem['type'] }) {
  if (type === 'email') {
    return (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="size-5 shrink-0">
        <path d="M1.5 8.67v8.58a3 3 0 0 0 3 3h15a3 3 0 0 0 3-3V8.67l-8.928 5.493a3 3 0 0 1-3.144 0L1.5 8.67Z" />
        <path d="M22.5 6.908V6.75a3 3 0 0 0-3-3h-15a3 3 0 0 0-3 3v.158l9.714 5.978a1.5 1.5 0 0 0 1.572 0L22.5 6.908Z" />
      </svg>
    )
  }
  if (type === 'home_assistant') {
    return (
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="size-5 shrink-0">
        <path d="M12 2.1 1 10.5V21h8v-6h6v6h8V10.5L12 2.1Zm0 2.532 7 5.363V19h-4v-6H9v6H5V9.995l7-5.363Z"/>
      </svg>
    )
  }
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="size-5 shrink-0">
      <path fillRule="evenodd" d="M2.25 5.25a3 3 0 0 1 3-3h13.5a3 3 0 0 1 3 3V15a3 3 0 0 1-3 3h-3v.257c0 .597.237 1.17.659 1.591l.621.622a.75.75 0 0 1-.53 1.28h-7.5a.75.75 0 0 1-.53-1.28l.621-.622a2.25 2.25 0 0 0 .659-1.59V18h-3a3 3 0 0 1-3-3V5.25Zm1.5 0v9.75c0 .828.672 1.5 1.5 1.5h13.5c.828 0 1.5-.672 1.5-1.5V5.25c0-.828-.672-1.5-1.5-1.5H5.25c-.828 0-1.5.672-1.5 1.5Z" clipRule="evenodd" />
    </svg>
  )
}

function notificationTitle(t: TFunction, n: NotificationListItem): string {
  switch (n.type) {
    case 'email': return t('notifications.emailType')
    case 'home_assistant': return t('notifications.haType')
    case 'browser': return t('notifications.browserType')
  }
}

function notificationSubtitle(t: TFunction, n: NotificationListItem): string {
  if (n.type === 'email') {
    const to = n.email_to ?? ''
    const subject = n.email_subject ? ` • ${n.email_subject}` : ''
    return t('notifications.emailTo', { email: to }) + subject
  }
  if (n.type === 'home_assistant') {
    const service = n.ha_notify_service ?? ''
    return `notify.${service}`
  }
  return t('notifications.browserSubtitle')
}

export function NotificationsPage() {
  const { t } = useTranslation()
  const [notifications, setNotifications] = useState<NotificationListItem[] | null>(null)
  const [configStatus, setConfigStatus] = useState<NotificationConfigStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [removeId, setRemoveId] = useState<number | null>(null)
  const [removing, setRemoving] = useState(false)

  async function refresh() {
    setError(null)
    try {
      const [data, status] = await Promise.all([listNotifications(), getNotificationConfigStatus()])
      setNotifications(data)
      setConfigStatus(status)
    } catch (e) {
      setNotifications([])
      setError(e instanceof Error ? e.message : t('notifications.errorLoading'))
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  const empty = useMemo(() => (notifications?.length ?? 0) === 0, [notifications])

  const hasEmail = notifications?.some((n) => n.type === 'email') ?? false
  const hasHa = notifications?.some((n) => n.type === 'home_assistant') ?? false

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">{t('notifications.title')}</h2>
          <p className="mt-1 text-sm text-gray-600">{t('notifications.description')}</p>
        </div>
        <Link
          to="/notifications/new"
          className="inline-flex items-center rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
        >
          {t('notifications.addNotification')}
        </Link>
      </div>

      {configStatus && (hasEmail || hasHa) ? (
        <div className="space-y-2">
          {hasEmail && !configStatus.email_configured ? (
            <div className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700 ring-1 ring-amber-200">
              {t('notifications.emailMissingConfig')}
            </div>
          ) : null}
          {hasHa && !configStatus.ha_configured ? (
            <div className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700 ring-1 ring-amber-200">
              {t('notifications.haMissingConfig')}
            </div>
          ) : null}
        </div>
      ) : null}

      {notifications == null ? (
        <div className="rounded-lg bg-white p-4 shadow-sm text-sm text-gray-600 ring-1 ring-black/5">{t('notifications.loading')}</div>
      ) : error ? (
        <div className="rounded-lg bg-white p-4 shadow-sm text-sm text-red-700 ring-1 ring-red-200">{error}</div>
      ) : empty ? (
        <div className="rounded-xl bg-white p-6 shadow-sm text-center ring-1 ring-black/5">
          <p className="text-sm text-gray-600">{t('notifications.noNotifications')}</p>
          <div className="mt-4">
            <Link
              to="/notifications/new"
              className="inline-flex items-center rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
            >
              {t('notifications.addNotification')}
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {notifications.map((n) => (
            <section
              key={n.id}
              className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-renfe-purple/20"
            >
              <div className="bg-renfeHeader px-4 py-3 text-white">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <NotificationIcon type={n.type} />
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold truncate">{n.label ? n.label : notificationTitle(t, n)}</h3>
                      <div className="text-xs text-white/85 truncate">{notificationSubtitle(t, n)}</div>
                    </div>
                  </div>
                  <span className="text-xs text-white/85">
                    {n.type === 'browser' ? t('notifications.browser') : t('notifications.alert')}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between gap-4 px-4 py-4">
                <div className="min-w-0">
                  {n.created_at ? (
                    <div className="text-xs text-gray-500">
                      {t('notifications.createdAt', { date: new Date(n.created_at).toLocaleString() })}
                    </div>
                  ) : null}
                </div>

                <button
                  type="button"
                  onClick={() => setRemoveId(n.id)}
                  className="rounded-md border border-gray-200 px-2.5 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
                >
                  {t('common.remove')}
                </button>
              </div>
            </section>
          ))}
        </div>
      )}

      <Dialog open={removeId != null} onClose={() => (removing ? null : setRemoveId(null))} className="relative z-50">
        <div className="fixed inset-0 bg-black/40" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <DialogPanel className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl ring-1 ring-black/5">
            <DialogTitle className="text-base font-semibold text-gray-900">{t('notifications.removeTitle')}</DialogTitle>
            <p className="mt-2 text-sm text-gray-600">{t('notifications.removeBody')}</p>

            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                disabled={removing}
                onClick={() => setRemoveId(null)}
                className="rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-60"
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                disabled={removing || removeId == null}
                onClick={async () => {
                  if (removeId == null) return
                  setRemoving(true)
                  try {
                    await deleteNotification(removeId)
                    setRemoveId(null)
                    await refresh()
                  } catch (e) {
                    setError(e instanceof Error ? e.message : t('notifications.errorCouldNotRemove'))
                    setRemoveId(null)
                  } finally {
                    setRemoving(false)
                  }
                }}
                className="rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover disabled:opacity-60"
              >
                {t('common.remove')}
              </button>
            </div>
          </DialogPanel>
        </div>
      </Dialog>
    </div>
  )
}
