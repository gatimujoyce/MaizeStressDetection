import { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useLoginMutation } from '../../api/hooks'
import { useAuth } from '../../auth/AuthContext'
import { jwtDecode } from 'jwt-decode'
import { EyeIcon, EyeOffIcon } from '../../components/Icons'

export default function Login() {
    const [phone, setPhone] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState('')
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const { login } = useAuth()
    const loginMutation = useLoginMutation()
    const registered = searchParams.get('registered') === 'true'

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        try {
            if (!/^\d{9}$/.test(phone)) {
                setError('Enter the 9 digits after +254')
                return
            }
            const data = await loginMutation.mutateAsync({ phone: `+254${phone}`, password })
            const token = data.access_token
            login(token)
            const { role } = jwtDecode(token)
            navigate(role === 'admin' ? '/admin' : '/', { replace: true })
        } catch (err) {
            setError(err.message || 'Phone number or password is incorrect')
        }
    }

    return (
        <div className="min-h-screen bg-[var(--color-bg)] flex items-center justify-center px-4">
            <div className="w-full max-w-sm bg-white border border-[var(--color-border)] rounded-sm p-8 shadow-sm">
                {/* Logo / brand */}
                <div className="mb-6 text-center">
                    <span className="text-2xl font-bold text-[var(--color-brand)]"> MaizeStressMonitor</span>
                    <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Field monitoring & disease detection</p>
                </div>

                {registered && (
                    <div className="mb-4 px-3 py-2 bg-[var(--color-healthy-bg)] text-[var(--color-healthy-text)] rounded-sm text-sm">
                        Account created successfully. You can now log in.
                    </div>
                )}

                {error && (
                    <div className="mb-4 px-3 py-2 bg-[var(--color-critical-bg)] text-[var(--color-critical-text)] rounded-sm text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                    <div className="flex flex-col gap-1">
                        <label htmlFor="phone" className="text-sm font-medium text-[var(--color-text-primary)]">
                            Phone number
                        </label>
                        <div className="relative">
                            <span className="absolute inset-y-0 left-3 flex items-center text-base text-[var(--color-text-secondary)]" aria-hidden="true">
                                +254
                            </span>
                            <input
                                id="phone"
                                type="tel"
                                inputMode="numeric"
                                maxLength={9}
                                value={phone}
                                onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 9))}
                                placeholder="712345678"
                                required
                                className="border border-[var(--color-border)] px-3 py-2 pl-16 rounded-sm text-base w-full focus:outline-none focus:border-[var(--color-brand)]"
                            />
                        </div>
                    </div>

                    <div className="flex flex-col gap-1">
                        <label htmlFor="password" className="text-sm font-medium text-[var(--color-text-primary)]">
                            Password
                        </label>
                        <div className="relative">
                            <input
                                id="password"
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="border border-[var(--color-border)] px-3 py-2 pr-16 rounded-sm text-base w-full focus:outline-none focus:border-[var(--color-brand)]"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword((visible) => !visible)}
                                aria-label={showPassword ? 'Hide password' : 'Show password'}
                                aria-pressed={showPassword}
                                className="absolute inset-y-0 right-3 text-sm font-medium text-[var(--color-brand)]"
                            >
                                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loginMutation.isPending}
                        className="bg-[var(--color-brand)] hover:bg-[var(--color-brand-hover)] text-white font-semibold py-2 px-4 rounded-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        {loginMutation.isPending ? 'Signing in…' : 'Sign in'}
                    </button>
                </form>

                <p className="mt-5 text-center text-sm text-[var(--color-text-secondary)]">
                    Don&apos;t have an account?{' '}
                    <Link to="/register" className="text-[var(--color-brand)] font-medium underline">
                        Register
                    </Link>
                </p>

                {/* Dev hint */}
                {import.meta.env.VITE_USE_MOCK_API === 'true' && (
                    <div className="mt-4 p-3 bg-[var(--color-neutral-bg)] rounded-sm text-xs text-[var(--color-text-secondary)]">
                        <strong>Mock mode:</strong><br />
                        Farmer: 712000001 / farmer123<br />
                        Admin: 712000002 / admin123
                    </div>
                )}
            </div>
        </div>
    )
}
