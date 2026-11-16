import NavBar from './NavBar'
import BottomNav from './BottomNav'
import OfflineNotice from './OfflineNotice'
import { useAuth } from '../auth/AuthContext'
import { useLocation } from 'react-router-dom'
import PasswordGate from './PasswordGate'

// The farmer frame: top bar, the page (each view sets its own width with <Page>), and the bottom bar on phones.
// Administrators get their own shell (AdminShell), and the sign-in screens bring their own layout.
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
          id="main-content"
          className={`px-gutter pt-6 sm:px-6 sm:pt-8 ${
            showBottomNav ? 'pb-[calc(6rem+env(safe-area-inset-bottom,0px))] sm:pb-12' : 'pb-12'
          }`}
        >
          {isAuthenticated && (
            <div className="mx-auto max-w-farmer empty:hidden [&>*]:mb-8">
              <OfflineNotice />
            </div>
          )}
          {children}
        </main>
      )}
      {showBottomNav && <BottomNav />}
      <PasswordGate />
    </div>
  )
}
