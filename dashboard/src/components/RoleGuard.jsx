import { useAuth } from '../auth/AuthContext'

export default function RoleGuard({ allowedRole, children }) {
  const { role } = useAuth()
  if (role !== allowedRole) {
    return <p>You don't have access to this view.</p>
  }
  return children
}