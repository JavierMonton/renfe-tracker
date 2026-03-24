import { Link, Route, Routes } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { HomePage } from './pages/HomePage'
import { ResultsPage } from './pages/ResultsPage'
import { SearchPage } from './pages/SearchPage'
import { TripDetailPage } from './pages/TripDetailPage'
import { NotificationsPage } from './pages/NotificationsPage'
import { NotificationCreatePage } from './pages/NotificationCreatePage'
import { BrowserNotificationsManager } from './BrowserNotificationsManager'

function App() {
  const { t, i18n } = useTranslation()

  function setLanguage(lang: string) {
    void i18n.changeLanguage(lang)
    localStorage.setItem('lang', lang)
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <BrowserNotificationsManager />
      <header className="bg-renfeHeader text-white shadow-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <h1 className="text-lg font-semibold">
            <Link to="/" className="text-white no-underline hover:no-underline">
              Renfe Tracker
            </Link>
          </h1>
          <nav className="flex items-center gap-4 text-sm font-medium">
            <Link to="/" className="text-white/90 hover:text-white">
              {t('nav.trips')}
            </Link>
            <Link to="/search" className="text-white/90 hover:text-white">
              {t('nav.search')}
            </Link>
            <Link to="/notifications" className="text-white/90 hover:text-white">
              {t('nav.notifications')}
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/notifications/new" element={<NotificationCreatePage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/trip/:id" element={<TripDetailPage />} />
        </Routes>
      </main>
      <footer className="mt-8 border-t border-stone-300 bg-stone-200 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4">
          <a
            href="https://github.com/JavierMonton/renfe-tracker"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-stone-500 hover:text-stone-800"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="size-5">
              <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.757-1.333-1.757-1.089-.745.083-.729.083-.729 1.205.084 1.84 1.236 1.84 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.418-1.305.762-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.605-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
            </svg>
            Check on GitHub
          </a>
          <a
            href="https://javiermonton.github.io/renfe-tracker"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-stone-500 hover:text-stone-800"
          >
            Documentation
          </a>
          <div className="flex items-center gap-1">
            {(['en', 'es', 'ca'] as const).map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => setLanguage(lang)}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-renfe-purple focus:ring-offset-2 ${
                  i18n.language === lang
                    ? 'bg-stone-400 text-stone-800'
                    : 'border border-stone-400 text-stone-600 hover:bg-stone-300'
                }`}
              >
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
