import { Dialog, DialogPanel, DialogTitle } from '@headlessui/react'
import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { createNotification, getNotificationConfigStatus } from '../api/client'
import type {
  CreateBrowserNotificationBody,
  CreateEmailNotificationBody,
  CreateHomeAssistantNotificationBody,
  NotificationConfigStatus,
  NotificationType,
} from '../api/types'

export function NotificationCreatePage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [type, setType] = useState<NotificationType>('email')
  const [label, setLabel] = useState('')

  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [configStatus, setConfigStatus] = useState<NotificationConfigStatus | null>(null)

  const webNotificationsSupported = useMemo(() => {
    return typeof window !== 'undefined' && typeof Notification !== 'undefined' && 'requestPermission' in Notification
  }, [])

  const [toEmail, setToEmail] = useState('')
  const [emailSubject, setEmailSubject] = useState('Price change alert')

  const [haNotifyService, setHaNotifyService] = useState('mobile_app')

  const [browserPermission, setBrowserPermission] = useState<NotificationPermission | 'unknown'>('unknown')

  const [savedOpen, setSavedOpen] = useState(false)
  const [savedSummary, setSavedSummary] = useState('')

  useEffect(() => {
    try {
      if (typeof Notification !== 'undefined') setBrowserPermission(Notification.permission)
    } catch {
      setBrowserPermission('unknown')
    }

    void getNotificationConfigStatus()
      .then(setConfigStatus)
      .catch(() => {/* non-critical */})
  }, [])

  function resetForAddAnother() {
    setError(null)
    setSaving(false)
    setSavedOpen(false)
    if (type === 'email') {
      setToEmail('')
      setEmailSubject('Price change alert')
    }
    if (type === 'home_assistant') {
      setHaNotifyService('mobile_app')
    }
    setLabel('')
  }

  function normalizeHomeAssistantNotifyService(service: string) {
    const s = service.trim()
    return s.replace(/^notify\./i, '')
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (saving) return

    setError(null)
    setSaving(true)
    try {
      const trimmedLabel = label.trim() || null

      if (type === 'email') {
        const to = toEmail.trim()
        const subject = emailSubject.trim()

        if (!to) { setError(t('notificationCreate.errorEmailRequired')); setSaving(false); return }
        if (!subject) { setError(t('notificationCreate.errorSubjectRequired')); setSaving(false); return }

        const body: CreateEmailNotificationBody = {
          type: 'email',
          label: trimmedLabel,
          email_to: to,
          email_subject: subject,
        }

        await createNotification(body)
        setSavedSummary(t('notificationCreate.savedEmailSummary', { to }))
        setSavedOpen(true)
        return
      }

      if (type === 'home_assistant') {
        const notifyService = normalizeHomeAssistantNotifyService(haNotifyService)

        if (!notifyService) { setError(t('notificationCreate.errorHaServiceRequired')); setSaving(false); return }

        const body: CreateHomeAssistantNotificationBody = {
          type: 'home_assistant',
          label: trimmedLabel,
          ha_notify_service: notifyService,
        }

        await createNotification(body)
        setSavedSummary(t('notificationCreate.savedHaSummary', { service: notifyService }))
        setSavedOpen(true)
        return
      }

      if (type === 'browser') {
        if (!webNotificationsSupported) {
          setError(t('notificationCreate.errorBrowserNotSupported'))
          setSaving(false)
          return
        }

        const next = await Notification.requestPermission()
        setBrowserPermission(next)
        const browserBody: CreateBrowserNotificationBody = {
          type: 'browser',
          label: trimmedLabel,
        }
        await createNotification(browserBody)
        setSavedSummary(
          next === 'granted'
            ? t('notificationCreate.savedBrowserGranted')
            : t('notificationCreate.savedBrowserDenied', { permission: next })
        )
        setSavedOpen(true)
        return
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t('notificationCreate.errorCouldNotSave'))
    } finally {
      setSaving(false)
    }
  }

  const browserEnabledLabel =
    browserPermission === 'granted'
      ? t('notificationCreate.permissionEnabled')
      : browserPermission === 'denied'
      ? t('notificationCreate.permissionDenied')
      : t('notificationCreate.permissionNotEnabled')

  const emailReady = configStatus?.email_configured ?? null
  const haReady = configStatus?.ha_configured ?? null

  function ConfigBanner({ configured, vars }: { configured: boolean | null; vars: string }) {
    if (configured === null) return null
    if (configured) {
      return (
        <div className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700 ring-1 ring-green-200">
          {t('notificationCreate.emailConfigured')}
        </div>
      )
    }
    return (
      <div className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700 ring-1 ring-amber-200">
        {t('notificationCreate.emailNotConfiguredBefore')}{' '}
        <span className="font-mono font-semibold">{vars}</span>{' '}
        {t('notificationCreate.emailNotConfiguredAfter')}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-gray-900">{t('notificationCreate.title')}</h2>
          <p className="mt-1 text-sm text-gray-600">{t('notificationCreate.description')}</p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/notifications')}
          className="rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
        >
          {t('notificationCreate.back')}
        </button>
      </div>

      <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-black/5">
        <form onSubmit={onSubmit} className="space-y-5">
          <fieldset>
            <legend className="text-sm font-semibold text-gray-900">{t('notificationCreate.notificationType')}</legend>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
              {(['email', 'home_assistant', 'browser'] as NotificationType[]).map((tp) => {
                const labelText =
                  tp === 'email'
                    ? t('notificationCreate.emailType')
                    : tp === 'home_assistant'
                    ? t('notificationCreate.haType')
                    : t('notificationCreate.browserType')
                return (
                  <label
                    key={tp}
                    className={`flex cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 text-sm font-medium shadow-sm ${
                      type === tp
                        ? 'border-renfe-purple bg-renfe-purple/5 text-gray-900 focus-within:ring-2 focus-within:ring-renfe-purple'
                        : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 focus-within:ring-2 focus-within:ring-renfe-purple/30'
                    }`}
                  >
                    <input
                      type="radio"
                      name="notification-type"
                      value={tp}
                      checked={type === tp}
                      onChange={() => {
                        setType(tp)
                        setError(null)
                      }}
                      className="h-4 w-4 border-gray-300 text-renfe-purple focus:ring-renfe-purple/30"
                    />
                    {labelText}
                  </label>
                )
              })}
            </div>
          </fieldset>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-900" htmlFor="notification-label">
                {t('notificationCreate.optionalLabel')}
              </label>
              <input
                id="notification-label"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="mt-1 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-renfe-purple focus:outline-none focus:ring-2 focus:ring-renfe-purple/30"
                placeholder={t('notificationCreate.labelPlaceholder')}
              />
            </div>
          </div>

          {error ? <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">{error}</div> : null}

          {type === 'email' ? (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-900">{t('notificationCreate.emailConfig')}</h3>

              <ConfigBanner
                configured={emailReady}
                vars="SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD"
              />

              <p className="text-sm text-gray-500">{t('notificationCreate.emailSmtpNote')}</p>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-900" htmlFor="email-to">
                    {t('notificationCreate.sendAlertsTo')}
                  </label>
                  <input
                    id="email-to"
                    type="email"
                    value={toEmail}
                    onChange={(e) => setToEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="mt-1 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-renfe-purple focus:outline-none focus:ring-2 focus:ring-renfe-purple/30"
                    required
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-900" htmlFor="email-subject">
                    {t('notificationCreate.subject')}
                  </label>
                  <input
                    id="email-subject"
                    value={emailSubject}
                    onChange={(e) => setEmailSubject(e.target.value)}
                    className="mt-1 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-renfe-purple focus:outline-none focus:ring-2 focus:ring-renfe-purple/30"
                    required
                  />
                </div>
              </div>
            </div>
          ) : null}

          {type === 'home_assistant' ? (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-900">{t('notificationCreate.haConfig')}</h3>

              <ConfigBanner
                configured={haReady}
                vars="HA_URL, HA_TOKEN"
              />

              <p className="text-sm text-gray-500">{t('notificationCreate.haNote')}</p>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-900" htmlFor="ha-notify-service">
                    {t('notificationCreate.notifyServiceName')}
                  </label>
                  <input
                    id="ha-notify-service"
                    value={haNotifyService}
                    onChange={(e) => setHaNotifyService(e.target.value)}
                    placeholder={t('notificationCreate.notifyServicePlaceholder')}
                    className="mt-1 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-renfe-purple focus:outline-none focus:ring-2 focus:ring-renfe-purple/30"
                    required
                  />
                  <div className="mt-1 text-xs text-gray-500">
                    {t('notificationCreate.notifyServiceHelp')}
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {type === 'browser' ? (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-gray-900">{t('notificationCreate.browserConfig')}</h3>
              <div className="rounded-lg bg-gray-50 p-4 ring-1 ring-gray-100">
                <p className="text-sm text-gray-700">{t('notificationCreate.browserDescription')}</p>
                <p className="mt-2 text-sm text-gray-600">
                  {t('notificationCreate.browserStatus', { status: browserEnabledLabel })}
                </p>
              </div>
            </div>
          ) : null}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              disabled={saving}
              onClick={() => navigate('/notifications')}
              className="rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-60"
            >
              {t('notificationCreate.cancel')}
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2"
            >
              {saving ? t('notificationCreate.saving') : t('notificationCreate.saveNotification')}
            </button>
          </div>
        </form>
      </section>

      <Dialog open={savedOpen} onClose={resetForAddAnother} className="relative z-50">
        <div className="fixed inset-0 bg-black/40" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <DialogPanel className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl ring-1 ring-black/5">
            <DialogTitle className="text-base font-semibold text-gray-900">{t('notificationCreate.savedTitle')}</DialogTitle>
            <p className="mt-2 text-sm text-gray-600">{savedSummary || t('notificationCreate.savedDefault')}</p>
            <div className="mt-5 flex justify-end gap-3">
              <button
                type="button"
                onClick={resetForAddAnother}
                className="rounded-md border border-gray-200 px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
              >
                {t('notificationCreate.addAnother')}
              </button>
              <button
                type="button"
                onClick={() => {
                  setSavedOpen(false)
                  navigate('/notifications')
                }}
                className="rounded-md bg-renfe-red px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-renfe-redHover"
              >
                {t('notificationCreate.backToList')}
              </button>
            </div>
          </DialogPanel>
        </div>
      </Dialog>
    </div>
  )
}
