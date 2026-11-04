import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useRegisterMutation } from '../../api/hooks'
import { requestRegisterCode } from '../../api/authFlow'
import AuthField from '../../components/AuthField'
import AuthLayout from '../../components/AuthLayout'

const RESEND_SECONDS = 60

export default function Register() {
    const [form, setForm] = useState({ name: '', phone: '', password: '', confirm: '' })
    const [errors, setErrors] = useState({})
    const [visiblePasswords, setVisiblePasswords] = useState({ password: false, confirm: false })
    const [step, setStep] = useState('details')
    const [code, setCode] = useState('')
    const [sending, setSending] = useState(false)
    const [wait, setWait] = useState(0)
    const navigate = useNavigate()
    const registerMutation = useRegisterMutation()

    useEffect(() => {
        if (wait <= 0) return undefined
        const timer = setTimeout(() => setWait((seconds) => seconds - 1), 1000)
        return () => clearTimeout(timer)
    }, [wait])

    const validate = () => {
        const e = {}
        if (!form.name.trim()) e.name = 'Name is required'
        if (!/^[17]\d{8}$/.test(form.phone)) e.phone = 'Enter 9 digits starting with 7 or 1, like 712345678'
        if (form.password.length < 8) e.password = 'Password must be at least 8 characters'
        if (form.password !== form.confirm) e.confirm = 'Passwords do not match'
        return e
    }

    const handleChange = (field) => (e) => {
        let value = e.target.value
        if (field === 'phone') {
            value = value.replace(/\D/g, '')
            if (value.startsWith('254')) value = value.slice(3)
            else if (value.startsWith('0')) value = value.slice(1)
            value = value.slice(0, 9)
        }
        setForm((prev) => ({ ...prev, [field]: value }))
        setErrors((prev) => ({ ...prev, [field]: undefined }))
    }

    const togglePasswordVisibility = (field) => {
        setVisiblePasswords((prev) => ({ ...prev, [field]: !prev[field] }))
    }

    // Step 1: check the details, then text a code to the phone.
    const sendCode = async (e) => {
        e?.preventDefault()
        const e2 = validate()
        if (Object.keys(e2).length > 0) { setErrors(e2); return }
        setSending(true)
        setErrors({})
        try {
            await requestRegisterCode(`+254${form.phone}`)
            setStep('code')
            setCode('')
            setWait(RESEND_SECONDS)
        } catch (err) {
            setErrors({ server: err.message || 'We could not send the code. Please try again.' })
        } finally {
            setSending(false)
        }
    }

    // Step 2: the code proves the number is theirs; then the account is made.
    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!/^\d{6}$/.test(code)) { setErrors({ code: 'The code is 6 digits' }); return }
        setErrors({})
        try {
            await registerMutation.mutateAsync({
                name: form.name,
                phone: `+254${form.phone}`,
                password: form.password,
                code,
            })
            navigate('/login?registered=true', { replace: true })
        } catch (err) {
            setErrors({ server: err.message || 'Registration failed. Please try again.' })
        }
    }

    const submitClass = 'min-h-12 bg-[var(--color-brand)] hover:bg-[var(--color-brand-hover)] text-white font-bold py-2 px-4 rounded-control transition-colors disabled:opacity-60'
    const linkClass = 'inline-flex min-h-12 items-center justify-center text-[var(--color-brand)] font-normal underline disabled:no-underline disabled:opacity-60'

    return (
        <AuthLayout subtitle={step === 'details' ? 'Create your farmer account' : 'Check your phone'}>
                {errors.server && (
                    <div role="alert" className="mb-4 px-3 py-2 bg-[var(--color-critical-bg)] text-[var(--color-critical-text)] rounded-control text-small">
                        {errors.server}
                    </div>
                )}

                {step === 'details' ? (
                    <form onSubmit={sendCode} className="flex flex-col gap-4">
                        <AuthField id="name" label="Full name" autoComplete="name" value={form.name} error={errors.name} onChange={handleChange('name')} placeholder="Jane Doe or John Doe" />
                        <AuthField id="phone" label="Phone number" type="tel" prefix="+254" inputMode="numeric" maxLength={16} autoComplete="tel-national" value={form.phone} error={errors.phone} onChange={handleChange('phone')} placeholder="712345678" hint="We will text a code to this number." />
                        <AuthField id="password" label="Password" type="password" autoComplete="new-password" hint="At least 8 characters." value={form.password} error={errors.password} onChange={handleChange('password')} visible={visiblePasswords.password} onToggleVisibility={() => togglePasswordVisibility('password')} />
                        <AuthField id="confirm" label="Confirm password" type="password" autoComplete="new-password" value={form.confirm} error={errors.confirm} onChange={handleChange('confirm')} visible={visiblePasswords.confirm} onToggleVisibility={() => togglePasswordVisibility('confirm')} />

                        <button type="submit" disabled={sending} className={submitClass}>
                            {sending ? 'Sending code…' : 'Send code'}
                        </button>
                    </form>
                ) : (
                    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                        <p className="m-0 text-small text-[var(--color-text-secondary)]">
                            We sent a 6-digit code to +254{form.phone}. It works for 10 minutes.
                        </p>
                        <AuthField id="register-code" label="6-digit code" inputMode="numeric" maxLength={6} autoComplete="one-time-code" value={code} error={errors.code}
                            onChange={(event) => { setCode(event.target.value.replace(/\D/g, '').slice(0, 6)); setErrors((prev) => ({ ...prev, code: undefined })) }} />
                        <button type="submit" disabled={registerMutation.isPending} className={submitClass}>
                            {registerMutation.isPending ? 'Creating account…' : 'Create account'}
                        </button>
                        <button type="button" disabled={sending || wait > 0} onClick={sendCode} className={linkClass}>
                            {wait > 0 ? `Send a new code in ${wait}s` : 'Send a new code'}
                        </button>
                        <button type="button" onClick={() => { setStep('details'); setErrors({}) }} className={linkClass}>
                            Change my number or details
                        </button>
                    </form>
                )}

                <p className="mt-5 text-center text-small text-[var(--color-text-secondary)]">
                    Already have an account?{' '}
                    <Link to="/login" className="inline-flex min-h-12 items-center text-[var(--color-brand)] font-normal underline">
                        Sign in
                    </Link>
                </p>
        </AuthLayout>
    )
}
