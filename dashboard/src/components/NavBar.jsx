import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useAlerts } from '../api/hooks'
import { useFarm } from '../farm/FarmContext'

export default function NavBar() {
  const { role, isAuthenticated, logout } = useAuth()
  const { selectedFarmId } = useFarm()
  const { data: alerts = [] } = useAlerts(role === 'farmer' ? selectedFarmId : null)
  const unreadCount = alerts.filter((alert) => alert.status !== 'acknowledged').length
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <nav className="bg-[var(--color-brand)] text-white shadow-md">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <span className="text-lg font-bold tracking-tight">MaizeStressMonitor</span>

          {isAuthenticated && role === 'farmer' && (
            <div className="hidden sm:flex items-center gap-4 text-sm font-medium">
              <Link to="/" className="hover:underline opacity-90 hover:opacity-100 focus-visible:outline-white">Home</Link>
              <Link to="/check-in" className="hover:underline opacity-90 hover:opacity-100 focus-visible:outline-white">Check-in</Link>
              <Link to="/trends" className="hover:underline opacity-90 hover:opacity-100 focus-visible:outline-white">Trends</Link>
              <Link to="/alerts" className="inline-flex items-center gap-2 hover:underline opacity-90 hover:opacity-100 focus-visible:outline-white">
                Alerts
                {unreadCount > 0 && (
                  <span aria-label={`${unreadCount} unread alerts`} className="rounded-full bg-white px-2 py-0.5 text-xs font-bold text-[var(--color-brand)]">
                    {unreadCount}
                  </span>
                )}
              </Link>
            </div>
          )}

          {isAuthenticated && role === 'admin' && (
            <div className="hidden sm:flex items-center gap-4 text-sm font-medium">
              <Link to="/admin" className="hover:underline opacity-90 hover:opacity-100 focus-visible:outline-white">Overview</Link>
            </div>
          )}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {isAuthenticated && (
            <>
              <span className="text-xs opacity-75 hidden sm:block">
                {role === 'admin' ? 'Admin' : 'Farmer'}
              </span>
              <button
                onClick={handleLogout}
                className="bg-white text-[var(--color-brand)] text-sm font-semibold px-3 py-1.5 rounded-sm hover:bg-gray-50 transition-colors border border-transparent focus-visible:outline-white"
              >
                Log out
              </button>
            </>
          )}
          {!isAuthenticated && (
            <Link
              to="/login"
              className="bg-white text-[var(--color-brand)] text-sm font-semibold px-3 py-1.5 rounded-sm hover:bg-gray-50 transition-colors focus-visible:outline-white"
            >
              Sign in
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}