import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function RoleGuard({ allowedRole, children }) {
  const { isAuthenticated, role } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (role !== allowedRole) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 text-center px-4">
        <div className="text-4xl">🔒</div>
        <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">
          Access Denied
        </h1>
        <p className="text-[var(--color-text-secondary)] max-w-sm">
          You don&apos;t have permission to view this page.
          {role === 'farmer' && (
            <> <a href="/" className="text-[var(--color-brand)] underline">Go to your dashboard</a>.</>
          )}
          {role === 'admin' && (
            <> <a href="/admin" className="text-[var(--color-brand)] underline">Go to admin portal</a>.</>
          )}
        </p>
      </div>
    )
  }

  return children
}