import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { useFarmerFarm, useCreateFarmMutation } from '../../api/hooks'
import { useState } from 'react'

const SOIL_TYPES = [
    { value: 'sandy_loam', label: 'Sandy loam', description: 'Drains quickly, dries out faster between waterings. Good for maize with regular irrigation.' },
    { value: 'clay', label: 'Clay', description: 'Holds water well, but may stay wet too long after heavy rain. Risk of waterlogging.' },
    { value: 'silty_clay', label: 'Silty clay', description: 'Moderate drainage, retains nutrients well. Common in river-adjacent fields.' },
    { value: 'loam', label: 'Loam', description: 'Balanced drainage and moisture. Ideal for most maize varieties.' },
    { value: 'sandy', label: 'Sandy', description: 'Very fast drainage, needs frequent watering. Nutrients wash out quickly.' },
]

export default function Onboarding() {
    const { userId } = useAuth()
    const navigate = useNavigate()
    const { data: existingFarm, isLoading: checkingFarm } = useFarmerFarm(userId)
    const createFarmMutation = useCreateFarmMutation()

    const [form, setForm] = useState({ farmName: '', location: '', soilType: '' })
    const [error, setError] = useState('')

    // Skip onboarding if farm already exists
    useEffect(() => {
        if (!checkingFarm && existingFarm) {
            navigate('/', { replace: true })
        }
    }, [existingFarm, checkingFarm, navigate])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        if (!form.farmName.trim()) { setError('Farm name is required'); return }
        if (!form.soilType) { setError('Please select a soil type'); return }
        try {
            await createFarmMutation.mutateAsync({
                farmerId: userId,
                farmName: form.farmName,
                location: form.location,
                soilType: form.soilType,
            })
            navigate('/', { replace: true })
        } catch (err) {
            setError(err.message || 'Could not create farm. Please try again.')
        }
    }

    if (checkingFarm) {
        return <div className="flex justify-center py-20 text-[var(--color-text-secondary)]">Checking account…</div>
    }

    return (
        <div className="max-w-lg mx-auto py-8">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Set up your farm</h1>
                <p className="text-[var(--color-text-secondary)] mt-1">
                    Tell us about your field so we can calibrate alerts correctly.
                </p>
            </div>

            {error && (
                <div className="mb-4 px-3 py-2 bg-[var(--color-critical-bg)] text-[var(--color-critical-text)] rounded-sm text-sm">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="flex flex-col gap-5 bg-white border border-[var(--color-border)] rounded-sm p-6">
                {/* Farm name */}
                <div className="flex flex-col gap-1">
                    <label htmlFor="farmName" className="text-sm font-medium text-[var(--color-text-primary)]">
                        Farm name
                    </label>
                    <input
                        id="farmName"
                        type="text"
                        value={form.farmName}
                        onChange={(e) => setForm(f => ({ ...f, farmName: e.target.value }))}
                        placeholder="e.g. Plot 1 - North Field"
                        className="border border-[var(--color-border)] px-3 py-2 rounded-sm text-base w-full focus:outline-none focus:border-[var(--color-brand)]"
                    />
                </div>

                {/* Location */}
                <div className="flex flex-col gap-1">
                    <label htmlFor="location" className="text-sm font-medium text-[var(--color-text-primary)]">
                        Location <span className="font-normal text-[var(--color-text-secondary)]">(optional)</span>
                    </label>
                    <input
                        id="location"
                        type="text"
                        value={form.location}
                        onChange={(e) => setForm(f => ({ ...f, location: e.target.value }))}
                        placeholder="e.g. Eldoret, Kenya"
                        className="border border-[var(--color-border)] px-3 py-2 rounded-sm text-base w-full focus:outline-none focus:border-[var(--color-brand)]"
                    />
                </div>

                {/* Soil type */}
                <div className="flex flex-col gap-2">
                    <span className="text-sm font-medium text-[var(--color-text-primary)]">Soil type</span>
                    <div className="flex flex-col gap-2">
                        {SOIL_TYPES.map((soil) => (
                            <label
                                key={soil.value}
                                className={`flex gap-3 p-3 border rounded-sm cursor-pointer transition-colors ${form.soilType === soil.value
                                        ? 'border-[var(--color-brand)] bg-[var(--color-neutral-bg)]'
                                        : 'border-[var(--color-border)] hover:bg-[var(--color-neutral-bg)]'
                                    }`}
                            >
                                <input
                                    type="radio"
                                    name="soilType"
                                    value={soil.value}
                                    checked={form.soilType === soil.value}
                                    onChange={() => setForm(f => ({ ...f, soilType: soil.value }))}
                                    className="mt-0.5 shrink-0 accent-[var(--color-brand)]"
                                />
                                <div>
                                    <div className="font-medium text-sm text-[var(--color-text-primary)]">{soil.label}</div>
                                    <div className="text-xs text-[var(--color-text-secondary)] mt-0.5">{soil.description}</div>
                                </div>
                            </label>
                        ))}
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={createFarmMutation.isPending}
                    className="bg-[var(--color-brand)] hover:bg-[var(--color-brand-hover)] text-white font-semibold py-2.5 px-4 rounded-sm transition-colors disabled:opacity-60"
                >
                    {createFarmMutation.isPending ? 'Setting up…' : 'Set up farm'}
                </button>
            </form>
        </div>
    )
}
