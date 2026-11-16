import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { linkClass } from './ui/styles'

export default function RoleGuard({ allowedRole, children }) {
  const { isAuthenticated, role } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (role !== allowedRole) {
    return (
      <div className="mx-auto flex max-w-farmer flex-col items-start gap-2 py-12">
        <h1 className="m-0 text-page text-ink">Access denied</h1>
        <p className="m-0 text-body text-ink-secondary">
          You don&apos;t have permission to view this page.
          {role === 'farmer' && (
            <> <a href="/" className={linkClass}>Go to your dashboard</a>.</>
          )}
          {role === 'admin' && (
            <> <a href="/admin" className={linkClass}>Go to admin portal</a>.</>
          )}
        </p>
      </div>
    )
  }

  return children
}