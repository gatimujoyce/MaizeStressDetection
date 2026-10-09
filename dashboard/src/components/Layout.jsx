import NavBar from './NavBar'
import BottomNav from './BottomNav'
import { useAuth } from '../auth/AuthContext'
import { useLocation } from 'react-router-dom'

export default function Layout({ children }) {
  const { role, isAuthenticated } = useAuth()
  const { pathname } = useLocation()
  const showBottomNav = isAuthenticated && role === 'farmer' && pathname !== '/onboarding'
  const isAuthScreen = pathname === '/login' || pathname === '/register'

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      {isAuthenticated && <NavBar />}
      {isAuthScreen ? children : (
        <main
          className={`max-w-6xl mx-auto px-4 pt-8 ${
            showBottomNav ? 'pb-[calc(6rem+env(safe-area-inset-bottom,0px))] sm:pb-8' : 'pb-8'
          }`}
        >
          {children}
        </main>
      )}
      {showBottomNav && <BottomNav />}
    </div>
  )
}