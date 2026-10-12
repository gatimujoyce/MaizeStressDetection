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
              <Link to="/" className="hover:underline opacity-90 hover:opacity-100 focus-visible:outline-white">Home</Link>
              <Link to="/check-in" className="hover:underline opacity-90 hover:opacity-100 focus-visible:outline-white">Check-in</Link>
              <Link to="/trends" className="hover:underline opacity-90 hover:opacity-100 focus-visible:outline-white">Trends</Link>
              <Link to="/alerts" className="hover:underline opacity-90 hover:opacity-100 focus-visible:outline-white">Alerts</Link>
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