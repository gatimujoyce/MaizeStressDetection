import { Link } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { useAlerts } from '../../api/hooks'
import { WarningIcon, InfoIcon, ErrorIcon } from '../../components/Icons'

const formatDate = (iso) =>
    new Date(iso).toLocaleString([], { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

export default function AlertsPage() {
    const { farmId } = useAuth()
    const { data: alerts = [], isLoading } = useAlerts(farmId || 'mock-farm-1')

    // Sort newest first
    const sorted = [...alerts].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

    const renderAlert = (alert) => {
        if (alert.status === 'uncertain' || alert.status === 'out_of_scope') {
            return (
                <div key={alert.alert_id} className="bg-[var(--color-neutral-bg)] border border-[var(--color-border)] rounded-sm p-4">
                    <div className="flex gap-2 items-center font-semibold text-[var(--color-neutral-text)] text-sm">
                        <InfoIcon size={14} />
                        <span>{alert.status === 'uncertain' ? 'Inconclusive Image Analysis' : 'Unrecognised Pattern'}</span>
                        <span className="ml-auto text-xs font-normal text-[var(--color-text-secondary)]">{formatDate(alert.created_at)}</span>
                    </div>
                    <p className="text-sm text-[var(--color-text-secondary)] mt-1">{alert.plain_summary}</p>
                    {alert.alert_id && (
                        <Link to={`/result/${alert.alert_id}`} className="mt-2 inline-block text-xs text-[var(--color-brand)] underline">
                            View full result
                        </Link>
                    )}
                </div>
            )
        }
        const isCritical = alert.severity === 'critical'
        return (
            <div
                key={alert.alert_id}
                className={`border border-[var(--color-border)] rounded-sm p-4 ${isCritical ? 'bg-[var(--color-critical-bg)]' : 'bg-[var(--color-warning-bg)]'}`}
            >
                <div className={`flex gap-2 items-center font-semibold text-sm ${isCritical ? 'text-[var(--color-critical-text)]' : 'text-[var(--color-warning-text)]'}`}>
                    {isCritical ? <ErrorIcon size={14} /> : <WarningIcon size={14} />}
                    <span>{alert.plain_summary}</span>
                    <span className="ml-auto text-xs font-normal text-[var(--color-text-secondary)]">{formatDate(alert.created_at)}</span>
                </div>
                <Link to={`/result/${alert.alert_id}`} className="mt-2 inline-block text-xs text-[var(--color-brand)] underline">
                    View result →
                </Link>
            </div>
        )
    }

    return (
        <div className="max-w-2xl mx-auto py-8">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">All Alerts</h1>
                <p className="text-[var(--color-text-secondary)] mt-1 text-sm">Your full alert history, newest first.</p>
            </div>

            {isLoading ? (
                <p className="text-[var(--color-text-secondary)] text-sm">Loading alerts…</p>
            ) : sorted.length === 0 ? (
                <p className="text-[var(--color-text-secondary)] text-sm">No alerts recorded yet.</p>
            ) : (
                <div className="flex flex-col gap-3">{sorted.map(renderAlert)}</div>
            )}
        </div>
    )
}
