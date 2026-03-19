import { Link, Route, Routes } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { ResultsPage } from './pages/ResultsPage'
import { SearchPage } from './pages/SearchPage'
import { TripDetailPage } from './pages/TripDetailPage'
import { NotificationsPage } from './pages/NotificationsPage'
import { NotificationCreatePage } from './pages/NotificationCreatePage'
import { BrowserNotificationsManager } from './BrowserNotificationsManager'

function App() {
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
              Trips
            </Link>
            <Link to="/search" className="text-white/90 hover:text-white">
              Search
            </Link>
            <Link to="/notifications" className="text-white/90 hover:text-white">
              Notifications
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
    </div>
  )
}

export default App
