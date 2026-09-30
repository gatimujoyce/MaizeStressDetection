import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useRegisterMutation } from '../../api/hooks'
import { EyeIcon, EyeOffIcon } from '../../components/Icons'

function Field({ id, label, type = 'text', placeholder, value, error, onChange, visible, onToggleVisibility, prefix, inputMode, maxLength }) {
    const isPassword = type === 'password'

    return (
        <div className="flex flex-col gap-1">
            <label htmlFor={id} className="text-sm font-medium text-[var(--color-text-primary)]">
                {label}
            </label>
            <div className={isPassword || prefix ? 'relative' : undefined}>
                <input
                    id={id}
                    type={isPassword && visible ? 'text' : type}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                    inputMode={inputMode}
                    maxLength={maxLength}
                    className={`border px-3 py-2 ${isPassword ? 'pr-16' : ''} ${prefix ? 'pl-16' : ''} rounded-sm text-base w-full focus:outline-none ${error
                        ? 'border-[var(--color-critical-text)]'
                        : 'border-[var(--color-border)] focus:border-[var(--color-brand)]'
                        }`}
                />
                {prefix && (
                    <span className="absolute inset-y-0 left-3 flex items-center text-base text-[var(--color-text-secondary)]" aria-hidden="true">
                        {prefix}
                    </span>
                )}
                {isPassword && (
                    <button
                        type="button"
                        onClick={onToggleVisibility}
                        aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
                        aria-pressed={visible}
                        className="absolute inset-y-0 right-3 text-sm font-medium text-[var(--color-brand)]"
                    >
                        {visible ? <EyeOffIcon /> : <EyeIcon />}
                    </button>
                )}
            </div>
            {error && (
                <p className="text-xs text-[var(--color-critical-text)]">{error}</p>
            )}
        </div>
    )
}

export default function Register() {
    const [form, setForm] = useState({ name: '', phone: '', password: '', confirm: '' })
    const [errors, setErrors] = useState({})
    const [visiblePasswords, setVisiblePasswords] = useState({ password: false, confirm: false })
    const navigate = useNavigate()
    const registerMutation = useRegisterMutation()

    const validate = () => {
        const e = {}
        if (!form.name.trim()) e.name = 'Name is required'
        if (!/^\d{9}$/.test(form.phone)) e.phone = 'Enter the 9 digits after +254'
        if (form.password.length < 6) e.password = 'Password must be at least 6 characters'
        if (form.password !== form.confirm) e.confirm = 'Passwords do not match'
        return e
    }

    const handleChange = (field) => (e) => {
        const value = field === 'phone'
            ? e.target.value.replace(/\D/g, '').slice(0, 9)
            : e.target.value
        setForm((prev) => ({ ...prev, [field]: value }))
        setErrors((prev) => ({ ...prev, [field]: undefined }))
    }

    const togglePasswordVisibility = (field) => {
        setVisiblePasswords((prev) => ({ ...prev, [field]: !prev[field] }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        const e2 = validate()
        if (Object.keys(e2).length > 0) { setErrors(e2); return }
        try {
            await registerMutation.mutateAsync({
                name: form.name,
                phone: `+254${form.phone}`,
                password: form.password,
            })
            navigate('/login?registered=true', { replace: true })
        } catch (err) {
            setErrors({ server: err.message || 'Registration failed. Please try again.' })
        }
    }

    return (
        <div className="min-h-screen bg-[var(--color-bg)] flex items-center justify-center px-4">
            <div className="w-full max-w-sm bg-white border border-[var(--color-border)] rounded-sm p-8 shadow-sm">
                <div className="mb-6 text-center">
                    <span className="text-2xl font-bold text-[var(--color-brand)]">MaizeStressMonitor</span>
                    <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Create your farmer account</p>
                </div>

                {errors.server && (
                    <div className="mb-4 px-3 py-2 bg-[var(--color-critical-bg)] text-[var(--color-critical-text)] rounded-sm text-sm">
                        {errors.server}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <Field id="name" label="Full name" value={form.name} error={errors.name} onChange={handleChange('name')} placeholder="Jane Doe or John Doe" />
                    <Field id="phone" label="Phone number" type="tel" prefix="+254" inputMode="numeric" maxLength={9} value={form.phone} error={errors.phone} onChange={handleChange('phone')} placeholder="712345678" />
                    <Field id="password" label="Password" type="password" value={form.password} error={errors.password} onChange={handleChange('password')} visible={visiblePasswords.password} onToggleVisibility={() => togglePasswordVisibility('password')} />
                    <Field id="confirm" label="Confirm password" type="password" value={form.confirm} error={errors.confirm} onChange={handleChange('confirm')} visible={visiblePasswords.confirm} onToggleVisibility={() => togglePasswordVisibility('confirm')} />

                    <button
                        type="submit"
                        disabled={registerMutation.isPending}
                        className="bg-[var(--color-brand)] hover:bg-[var(--color-brand-hover)] text-white font-semibold py-2 px-4 rounded-sm transition-colors disabled:opacity-60"
                    >
                        {registerMutation.isPending ? 'Creating account…' : 'Create account'}
                    </button>
                </form>

                <p className="mt-5 text-center text-sm text-[var(--color-text-secondary)]">
                    Already have an account?{' '}
                    <Link to="/login" className="text-[var(--color-brand)] font-medium underline">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    )
}
