import { useAuth } from '../auth/AuthContext'
import ChangePasswordDialog from './ChangePasswordDialog'

// Shows the "choose your own password" card, which cannot be closed, to anyone signed in with a temporary password.
export default function PasswordGate() {
    const { isAuthenticated, profile } = useAuth()
    if (!isAuthenticated || !profile?.must_change_password) return null
    return <ChangePasswordDialog forced />
}
