import { useFarmHistory } from '../../api/hooks'
import TrendChart from '../../components/TrendChart'
import { useFarm } from '../../farm/FarmContext'

export default function TrendsPage() {
    const { selectedFarmId, selectedFarm } = useFarm()
    const { data: history = [], isLoading } = useFarmHistory(selectedFarmId)

    return (
        <div className="max-w-2xl mx-auto py-8">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Field Trends</h1>
                <p className="mt-1 text-[15px] text-ink-secondary">Plot: {selectedFarm?.farm_name || 'Your field'}</p>
                <p className="text-[var(--color-text-secondary)] mt-1 text-sm">Full historical view of your field's health scores.</p>
            </div>

            {isLoading ? (
                <p className="text-[var(--color-text-secondary)] text-sm">Loading history…</p>
            ) : (
                <TrendChart history={history} />
            )}
        </div>
    )
}
