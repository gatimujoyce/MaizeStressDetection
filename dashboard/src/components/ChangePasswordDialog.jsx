import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { changePassword } from '../api/authFlow'
import { useAuth } from '../auth/AuthContext'
import AuthField from './AuthField'
import Modal from './ui/Modal'
import Notice from './ui/Notice'
import { buttonClass } from './ui/styles'


// Change your own password. With forced = true (a temporary password) it cannot be closed until a new one is chosen.
export default function ChangePasswordDialog({ forced = false, onClose }) {
    const { refreshProfile, logout } = useAuth()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const [form, setForm] = useState({ current: '', next: '', confirm: '' })
    const [show, setShow] = useState(false)
    const [error, setError] = useState('')
    const [done, setDone] = useState(false)
    const [busy, setBusy] = useState(false)

    const set = (key) => (event) => { setForm((prev) => ({ ...prev, [key]: event.target.value })); setError('') }

    async function handleSubmit(event) {
        event.preventDefault()
        if (form.next.length < 8) { setError('The new password must be at least 8 characters'); return }
        if (form.next !== form.confirm) { setError('The new passwords do not match'); return }
        if (form.next === form.current) { setError('Choose a password different from the current one'); return }
        setBusy(true)
        try {
            await changePassword({ currentPassword: form.current, newPassword: form.next })
            await refreshProfile?.()
            queryClient.invalidateQueries()
            setDone(true)
            if (forced) onClose?.()
        } catch (err) {
            setError(err.message || 'The password could not be changed. Try again.')
        } finally {
            setBusy(false)
        }
    }

    const title = forced ? 'Choose your own password' : 'Change password'

    return (
        <Modal title={title} onClose={onClose} dismissible={!forced}>
            {done ? (
                <div className="flex flex-col gap-4">
                    <Notice tone="positive"><p>Your password was changed.</p></Notice>
                    <button type="button" onClick={onClose} className={buttonClass({ block: true })}>Done</button>
                </div>
            ) : (
                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    {forced && (
                        <p className="m-0 text-small text-ink-secondary">
                            You signed in with a temporary password. Enter it below as the current password, then choose a new one that only you know.
                        </p>
                    )}
                    {error && <Notice tone="critical"><p>{error}</p></Notice>}
                    <AuthField id="cp-current" label={forced ? 'Temporary password' : 'Current password'} type="password" autoComplete="current-password" value={form.current} onChange={set('current')} visible={show} onToggleVisibility={() => setShow((value) => !value)} />
                    <AuthField id="cp-new" label="New password" type="password" autoComplete="new-password" hint="At least 8 characters." value={form.next} onChange={set('next')} visible={show} onToggleVisibility={() => setShow((value) => !value)} />
                    <AuthField id="cp-confirm" label="Confirm new password" type="password" autoComplete="new-password" value={form.confirm} onChange={set('confirm')} visible={show} onToggleVisibility={() => setShow((value) => !value)} />
                    <div className="flex flex-wrap gap-3">
                        <button type="submit" disabled={busy} className={`${buttonClass()} flex-1`}>{busy ? 'Saving…' : 'Save new password'}</button>
                        {forced
                            ? <button type="button" onClick={() => { logout(); navigate('/login', { replace: true }) }} className={buttonClass({ variant: 'secondary' })}>Sign out</button>
                            : <button type="button" onClick={onClose} className={buttonClass({ variant: 'secondary' })}>Cancel</button>}
                    </div>
                </form>
            )}
        </Modal>
    )
}
