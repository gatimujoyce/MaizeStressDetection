import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { requestPasswordResetCode, resetPassword } from '../../api/authFlow'
import AuthField from '../../components/AuthField'
import AuthLayout from '../../components/AuthLayout'

const RESEND_SECONDS = 60
const bannerClass = 'mb-4 px-3 py-2 rounded-control text-small'

// Forgot password: enter the phone, then the 6-digit code from the text message and a new password.
export default function ForgotPassword() {
    const navigate = useNavigate()
    const [step, setStep] = useState('phone')
    const [phone, setPhone] = useState('')
    const [code, setCode] = useState('')
    const [password, setPassword] = useState('')
    const [confirm, setConfirm] = useState('')
    const [show, setShow] = useState(false)
    const [error, setError] = useState('')
    const [busy, setBusy] = useState(false)
    const [wait, setWait] = useState(0)

    useEffect(() => {
        if (wait <= 0) return undefined
        const timer = setTimeout(() => setWait((seconds) => seconds - 1), 1000)
        return () => clearTimeout(timer)
    }, [wait])

    async function sendCode(event) {
        event?.preventDefault()
        setError('')
        if (!/^[17]\d{8}$/.test(phone)) { setError('Enter 9 digits starting with 7 or 1, like 712345678'); return }
        setBusy(true)
        try {
            await requestPasswordResetCode(`+254${phone}`)
            setStep('code')
            setWait(RESEND_SECONDS)
        } catch (err) {
            setError(err.message || 'Could not send the code. Try again.')
        } finally {
            setBusy(false)
        }
    }

    async function submitReset(event) {
        event.preventDefault()
        setError('')
        if (!/^\d{6}$/.test(code)) { setError('The code is 6 digits'); return }
        if (password.length < 8) { setError('Password must be at least 8 characters'); return }
        if (password !== confirm) { setError('Passwords do not match'); return }
        setBusy(true)
        try {
            await resetPassword({ phone: `+254${phone}`, code, newPassword: password })
            navigate('/login?reset=true', { replace: true })
        } catch (err) {
            setError(err.message || 'Could not change the password. Try again.')
        } finally {
            setBusy(false)
        }
    }

    const submitClass = 'min-h-12 bg-[var(--color-brand)] hover:bg-[var(--color-brand-hover)] text-white font-bold py-2 px-4 rounded-control transition-colors disabled:opacity-60'
    const linkClass = 'inline-flex min-h-12 items-center text-[var(--color-brand)] font-normal underline'

    return (
        <AuthLayout subtitle="Forgot your password?">
            {error && <div role="alert" className={`${bannerClass} bg-[var(--color-critical-bg)] text-[var(--color-critical-text)]`}>{error}</div>}

            {step === 'phone' ? (
                <form onSubmit={sendCode} className="flex flex-col gap-4">
                    <p className="m-0 text-small text-[var(--color-text-secondary)]">
                        Enter your phone number and we will text you a 6-digit code.
                    </p>
                    <AuthField id="forgot-phone" label="Phone number" type="tel" prefix="+254" inputMode="numeric" maxLength={16} autoComplete="tel-national" placeholder="712345678" value={phone}
                        onChange={(event) => {
                            let value = event.target.value.replace(/\D/g, '')
                            if (value.startsWith('254')) value = value.slice(3)
                            else if (value.startsWith('0')) value = value.slice(1)
                            setPhone(value.slice(0, 9))
                        }} />
                    <button type="submit" disabled={busy} className={submitClass}>{busy ? 'Sending…' : 'Send code'}</button>
                </form>
            ) : (
                <form onSubmit={submitReset} className="flex flex-col gap-4">
                    <p className="m-0 text-small text-[var(--color-text-secondary)]">
                        If +254{phone} has an account, a code is on its way. It works for 10 minutes.
                    </p>
                    <AuthField id="forgot-code" label="6-digit code" inputMode="numeric" maxLength={6} autoComplete="one-time-code" value={code}
                        onChange={(event) => setCode(event.target.value.replace(/\D/g, '').slice(0, 6))} />
                    <AuthField id="forgot-password" label="New password" type="password" autoComplete="new-password" hint="At least 8 characters." value={password}
                        onChange={(event) => setPassword(event.target.value)} visible={show} onToggleVisibility={() => setShow((value) => !value)} />
                    <AuthField id="forgot-confirm" label="Confirm new password" type="password" autoComplete="new-password" value={confirm}
                        onChange={(event) => setConfirm(event.target.value)} visible={show} onToggleVisibility={() => setShow((value) => !value)} />
                    <button type="submit" disabled={busy} className={submitClass}>{busy ? 'Saving…' : 'Change password'}</button>
                    <button type="button" disabled={busy || wait > 0} onClick={sendCode} className={`${linkClass} justify-center disabled:no-underline disabled:opacity-60`}>
                        {wait > 0 ? `Send a new code in ${wait}s` : 'Send a new code'}
                    </button>
                </form>
            )}

            <p className="mt-5 text-center text-small text-[var(--color-text-secondary)]">
                <Link to="/login" className={linkClass}>Back to sign in</Link>
            </p>
        </AuthLayout>
    )
}
