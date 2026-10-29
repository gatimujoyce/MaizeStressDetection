import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useAlerts } from '../api/hooks'
import { useFarm } from '../farm/FarmContext'

const navClass = ({ isActive }) =>
  `inline-flex min-h-11 items-center gap-2 rounded-control px-2 underline-offset-8 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-white ${isActive ? 'underline decoration-2' : 'opacity-90 hover:opacity-100'}`

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
    <nav className="bg-brand text-white">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <span className="text-heading tracking-tight">MaizeStressMonitor</span>

          {isAuthenticated && role === 'farmer' && (
            <div className="hidden sm:flex items-center gap-2 text-small font-bold">
              <NavLink to="/" end className={navClass}>Home</NavLink>
              <NavLink to="/check-in" className={navClass}>Check-in</NavLink>
              <NavLink to="/trends" className={navClass}>Trends</NavLink>
              <NavLink to="/alerts" className={navClass}>
                Alerts
                {unreadCount > 0 && (
                  <span aria-label={`${unreadCount} unread alerts`} className="rounded-full bg-white px-2 py-0.5 text-caption font-bold text-[var(--color-brand)]">
                    {unreadCount}
                  </span>
                )}
              </NavLink>
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
              <span className="hidden text-small opacity-90 sm:block">
                {role === 'admin' ? 'Admin' : 'Farmer'}
              </span>
              <button
                onClick={handleLogout}
                className="min-h-11 rounded-control border border-transparent bg-white px-4 text-small font-bold text-brand transition-colors duration-fast hover:bg-brand-tint focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                Log out
              </button>
            </>
          )}
          {!isAuthenticated && (
            <Link
              to="/login"
              className="inline-flex min-h-11 items-center rounded-control bg-white px-4 text-small font-bold text-brand transition-colors duration-fast hover:bg-brand-tint focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              Sign in
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}