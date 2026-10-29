import { useFarmHistory } from '../../api/hooks'
import TrendChart from '../../components/TrendChart'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { useFarm } from '../../farm/FarmContext'

export default function TrendsPage() {
    const { selectedFarmId, selectedFarm } = useFarm()
    const { data: history = [], isLoading } = useFarmHistory(selectedFarmId)

    return (
        <div className="mx-auto flex max-w-2xl flex-col gap-6">
            <div>
                <PageHeader title="Field Trends" subtitle={`Plot: ${selectedFarm?.farm_name || 'Your field'}`} />
                <p className="m-0 mt-1 text-small text-ink-secondary">Full historical view of your field's health scores.</p>
            </div>

            {isLoading ? (
                <Skeleton label="Loading history…" className="h-48" />
            ) : (
                <TrendChart history={history} />
            )}
        </div>
    )
}
