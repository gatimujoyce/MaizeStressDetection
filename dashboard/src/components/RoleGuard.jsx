import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { InfoIcon } from './Icons'

export default function RoleGuard({ allowedRole, children }) {
  const { isAuthenticated, role } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (role !== allowedRole) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 text-center px-4">
        <span aria-hidden="true" className="flex h-14 w-14 items-center justify-center rounded-full bg-neutral-bg text-neutral-text"><InfoIcon size={28} /></span>
        <h1 className="m-0 text-title text-ink">
          Access Denied
        </h1>
        <p className="m-0 max-w-sm text-body text-ink-secondary">
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