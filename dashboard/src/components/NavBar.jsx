import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function NavBar() {
  const { role, isAuthenticated, logout } = useAuth()
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
              <Link to="/" className="hover:underline opacity-90 hover:opacity-100">Dashboard</Link>
              <Link to="/check-in" className="hover:underline opacity-90 hover:opacity-100">Check-in</Link>
              <Link to="/trends" className="hover:underline opacity-90 hover:opacity-100">Trends</Link>
              <Link to="/alerts" className="hover:underline opacity-90 hover:opacity-100">Alerts</Link>
            </div>
          )}

          {isAuthenticated && role === 'admin' && (
            <div className="hidden sm:flex items-center gap-4 text-sm font-medium">
              <Link to="/admin" className="hover:underline opacity-90 hover:opacity-100">Overview</Link>
              <Link to="/admin/users-farms" className="hover:underline opacity-90 hover:opacity-100">Users & Farms</Link>
              <Link to="/admin/models" className="hover:underline opacity-90 hover:opacity-100">Models</Link>
              <Link to="/admin/feedback" className="hover:underline opacity-90 hover:opacity-100">Feedback</Link>
              <Link to="/admin/retraining" className="hover:underline opacity-90 hover:opacity-100">Retraining</Link>
              <Link to="/admin/sms-log" className="hover:underline opacity-90 hover:opacity-100">SMS Log</Link>
            </div>
          )}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {isAuthenticated && (
            <>
              <span className="text-xs opacity-75 hidden sm:block">
                {role === 'admin' ? '👤 Admin' : '🌱 Farmer'}
              </span>
              <button
                onClick={handleLogout}
                className="bg-white text-[var(--color-brand)] text-sm font-semibold px-3 py-1.5 rounded-sm hover:bg-gray-50 transition-colors border border-transparent"
              >
                Log out
              </button>
            </>
          )}
          {!isAuthenticated && (
            <Link
              to="/login"
              className="bg-white text-[var(--color-brand)] text-sm font-semibold px-3 py-1.5 rounded-sm hover:bg-gray-50 transition-colors"
            >
              Sign in
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}