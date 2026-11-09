import NavBar from './NavBar'
import BottomNav from './BottomNav'
import OfflineNotice from './OfflineNotice'
import { useAuth } from '../auth/AuthContext'
import { useLocation } from 'react-router-dom'
import { useState } from 'react'
import PasswordGate from './PasswordGate'
import ChangePasswordDialog from './ChangePasswordDialog'
import FollowUpCard from './FollowUpCard'

export default function Layout({ children }) {
  const { role, isAuthenticated } = useAuth()
  const { pathname } = useLocation()
  const [changingPassword, setChangingPassword] = useState(false)
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
          {isAuthenticated && !isAdmin && (
            <div className="mb-2 flex justify-end">
              <button type="button" onClick={() => setChangingPassword(true)} className="min-h-11 text-small text-[var(--color-brand)] underline">
                Change password
              </button>
            </div>
          )}
          {changingPassword && <ChangePasswordDialog onClose={() => setChangingPassword(false)} />}
          {isAuthenticated && !isAdmin && (pathname === '/' || pathname === '/alerts') && <FollowUpCard />}
          {children}
        </main>
      )}
      {showBottomNav && <BottomNav />}
      <PasswordGate />
    </div>
  )
}
