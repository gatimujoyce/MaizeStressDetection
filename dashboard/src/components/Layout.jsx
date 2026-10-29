import NavBar from './NavBar'
import BottomNav from './BottomNav'
import OfflineNotice from './OfflineNotice'
import { useAuth } from '../auth/AuthContext'
import { useLocation } from 'react-router-dom'

export default function Layout({ children }) {
  const { role, isAuthenticated } = useAuth()
  const { pathname } = useLocation()
  const showBottomNav = isAuthenticated && role === 'farmer' && pathname !== '/onboarding'
  const isAuthScreen = pathname === '/login' || pathname === '/register'
  const isAdmin = isAuthenticated && role === 'admin'

  return (
    <div className="min-h-screen bg-app-bg">
      {isAuthenticated && !isAdmin && <NavBar />}
      {isAuthScreen || isAdmin ? children : (
        <main
          className={`mx-auto max-w-6xl px-4 pt-6 sm:pt-8 ${
            showBottomNav ? 'pb-[calc(6rem+env(safe-area-inset-bottom,0px))] sm:pb-10' : 'pb-10'
          }`}
        >
          {isAuthenticated && <OfflineNotice />}
          {children}
        </main>
      )}
      {showBottomNav && <BottomNav />}
    </div>
  )
}
