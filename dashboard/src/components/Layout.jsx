import NavBar from './NavBar'
import { useAuth } from '../auth/AuthContext'

export default function Layout({ children }) {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      {isAuthenticated && <NavBar />}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  )
}