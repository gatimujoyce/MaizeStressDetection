import { Link } from 'react-router-dom'
import { useAcknowledgeAlertMutation, useAlerts } from '../../api/hooks'
import { WarningIcon, ErrorIcon } from '../../components/Icons'
import { useFarm } from '../../farm/FarmContext'

export default function AlertsPage() {
    const { selectedFarmId, selectedFarm } = useFarm()
    const {
        data: alerts = [],
        isLoading,
        isError,
        isFetching,
        refetch,
    } = useAlerts(selectedFarmId)
    const acknowledgeMutation = useAcknowledgeAlertMutation(selectedFarmId)

    const sorted = [...alerts]

    const renderAlert = (alert) => {
        const isCritical = alert.severity === 'critical'
        return (
            <div
                key={alert.alert_id}
                className={`border border-[var(--color-border)] rounded-sm p-4 ${isCritical ? 'bg-[var(--color-critical-bg)]' : 'bg-[var(--color-warning-bg)]'}`}
            >
                <div className={`flex gap-2 items-center font-semibold text-sm ${isCritical ? 'text-[var(--color-critical-text)]' : 'text-[var(--color-warning-text)]'}`}>
                    {isCritical ? <ErrorIcon size={14} /> : <WarningIcon size={14} />}
                    <span>{alert.severity_label}</span>
                </div>
                {alert.prediction_id && <Link to={`/result/${alert.prediction_id}`} className="mt-2 inline-block text-xs text-[var(--color-brand)] underline">
                    View result →
                </Link>}
                {alert.status !== 'acknowledged' && (
                    <button
                        type="button"
                        onClick={() => acknowledgeMutation.mutate(alert.alert_id)}
                        disabled={acknowledgeMutation.isPending}
                        className="mt-3 min-h-11 rounded-xl border border-brand px-4 py-2 text-sm font-semibold text-brand disabled:opacity-60"
                    >
                        {acknowledgeMutation.isPending ? 'Acknowledging…' : 'Mark as read'}
                    </button>
                )}
            </div>
        )
    }

    return (
        <div className="max-w-2xl mx-auto py-8">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">All Alerts</h1>
                <p className="mt-1 text-[15px] text-ink-secondary">Plot: {selectedFarm?.farm_name || 'Your field'}</p>
                <p className="text-[var(--color-text-secondary)] mt-1 text-sm">Your full alert history, newest first.</p>
            </div>

            {isLoading ? (
                <p className="text-[var(--color-text-secondary)] text-sm">Loading alerts…</p>
            ) : isError ? (
                <div role="alert" className="text-[var(--color-critical-text)] text-sm">
                    <p>Could not load alerts.</p>
                    <button
                        type="button"
                        onClick={() => refetch()}
                        disabled={isFetching}
                        className="min-h-11 rounded-xl border border-brand px-4 py-2 font-semibold text-brand disabled:opacity-60"
                    >
                        {isFetching ? 'Retrying…' : 'Retry'}
                    </button>
                </div>
            ) : sorted.length === 0 ? (
                <p className="text-[var(--color-text-secondary)] text-sm">No alerts recorded yet.</p>
            ) : (
                <div className="flex flex-col gap-3">{sorted.map(renderAlert)}</div>
            )}
            {acknowledgeMutation.isError && (
                <p role="alert" className="mt-3 text-[var(--color-critical-text)] text-sm">
                    Could not acknowledge this alert. Please try again.
                </p>
            )}
        </div>
    )
}
