import { Link } from 'react-router-dom'
import { useAcknowledgeAlertMutation, useAlerts } from '../../api/hooks'
import AttentionAlert from '../../components/AttentionAlert'
import Notice from '../../components/ui/Notice'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { buttonClass, linkClass } from '../../components/ui/styles'
import useArrivals from '../../components/ui/useArrivals'
import { useFarm } from '../../farm/FarmContext'

const STRESS_TITLES = {
    heat_stress: 'Heat stress',
    drought_stress: 'Drought stress',
    waterlogging_risk: 'Waterlogging risk',
    low_nitrogen: 'Low nitrogen',
    low_phosphorus: 'Low phosphorus',
    low_potassium: 'Low potassium',
}

function timeOf(value) {
    const t = Date.parse(value)
    return Number.isNaN(t) ? null : t
}

// "2 hours ago" for today, "Yesterday 5:07 pm" for yesterday, "12 Oct" after that.
function formatWhen(value) {
    const t = timeOf(value)
    if (t === null) return ''
    const date = new Date(t)
    const now = new Date()
    const minutes = Math.round((now - date) / 60000)
    const clock = date.toLocaleTimeString('en-KE', { hour: 'numeric', minute: '2-digit' })
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes} min ago`
    if (minutes < 360) return `${Math.floor(minutes / 60)} hours ago`
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    if (date >= startOfToday) return `Today ${clock}`
    const startOfYesterday = new Date(startOfToday - 86400000)
    if (date >= startOfYesterday) return `Yesterday ${clock}`
    return `${date.toLocaleDateString('en-KE', { day: 'numeric', month: 'short' })} ${clock}`
}

function byNewest(a, b) {
    return (timeOf(b.created_at) || 0) - (timeOf(a.created_at) || 0)
}

function Stripe({ critical }) {
    return (
        <span
            aria-hidden="true"
            className={`absolute inset-y-0 left-0 w-1.5 ${critical ? 'bg-critical-text' : 'bg-warning-text'}`}
        />
    )
}

function SectionLabel({ id, children }) {
    return (
        <h2 id={id} className="mb-3 mt-0 text-heading text-ink-secondary">
            {children}
        </h2>
    )
}

export default function AlertsPage() {
    const { selectedFarmId, selectedFarm } = useFarm()
    const { data: alerts = [], isLoading, isSuccess, isError, isFetching, refetch } = useAlerts(selectedFarmId)
    const acknowledgeMutation = useAcknowledgeAlertMutation(selectedFarmId)
    const arrived = useArrivals(alerts.map((a) => a.alert_id), isSuccess)

    const sorted = [...alerts].sort(byNewest)
    const isOngoing = (a) => a.source === 'sensor' && !a.resolved_at
    const ongoing = sorted.filter(isOngoing)
    const earlier = sorted.filter((a) => !isOngoing(a))

    const renderEarlier = (alert) => {
        const critical = alert.severity === 'critical'
        const sensor = alert.source === 'sensor'
        const title = sensor
            ? `${STRESS_TITLES[alert.stress_class] || 'Field alert'}${alert.resolved_at ? ' (cleared)' : ''}`
            : `Photo check-in · ${alert.severity_label}`
        const unread = alert.status !== 'acknowledged'
        return (
            <li
                key={alert.alert_id}
                className={`relative flex flex-wrap items-center gap-x-4 gap-y-2 overflow-hidden rounded-card border border-border bg-surface py-3 pl-6 pr-4 ${arrived(alert.alert_id) ? 'motion-enter' : ''}`}
            >
                <Stripe critical={critical} />
                <div className="min-w-0 flex-1 basis-48">
                    <p className="m-0 flex items-center gap-2 text-body font-bold text-ink">
                        {unread && <span aria-label="Unread" className="inline-block h-2.5 w-2.5 shrink-0 rounded-full bg-brand" />}
                        {title}
                    </p>
                    <p className="m-0 text-small text-ink-secondary">
                        {formatWhen(alert.created_at)}
                        {alert.resolved_at ? ` · cleared ${formatWhen(alert.resolved_at)}` : ''}
                    </p>
                    {!sensor && alert.message && (
                        <p className="m-0 mt-1 text-small text-ink">{alert.message}</p>
                    )}
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                    {alert.prediction_id && (
                        <Link to={`/result/${selectedFarmId}/${alert.prediction_id}`} className={`inline-flex min-h-11 items-center text-small ${linkClass}`}>
                            View result →
                        </Link>
                    )}
                    {unread && (
                        <button
                            type="button"
                            onClick={() => acknowledgeMutation.mutate(alert.alert_id)}
                            disabled={acknowledgeMutation.isPending}
                            className={buttonClass({ variant: 'quiet', size: 'sm' })}
                        >
                            Mark as read
                        </button>
                    )}
                </div>
            </li>
        )
    }

    return (
        <div className="mx-auto flex max-w-2xl flex-col gap-6">
            <PageHeader
                title="Alerts"
                subtitle={`${selectedFarm?.farm_name || 'Your field'}${ongoing.length > 0 ? ` · ${ongoing.length} need${ongoing.length === 1 ? 's' : ''} attention now` : ''}`}
            />

            {isLoading ? (
                <div className="flex flex-col gap-3">
                    <Skeleton label="Loading alerts…" className="h-32" />
                    <Skeleton className="h-16" />
                    <Skeleton className="h-16" />
                </div>
            ) : isError ? (
                <Notice tone="critical" onRetry={() => refetch()} retrying={isFetching}>
                    <p>Could not load alerts.</p>
                </Notice>
            ) : (
                <>
                    <section aria-labelledby="now-heading">
                        <SectionLabel id="now-heading">Needs attention now</SectionLabel>
                        {ongoing.length === 0 ? (
                            <p className="m-0 rounded-card border border-border bg-surface p-4 text-body text-ink">
                                Nothing needs your attention right now. We are watching your field and will alert you here.
                            </p>
                        ) : (
                            <div className="flex flex-col gap-3">
                                {ongoing.map((alert) => (
                                    <AttentionAlert
                                        key={alert.alert_id}
                                        alert={alert}
                                        farmId={selectedFarmId}
                                        meta={`Ongoing · started ${formatWhen(alert.created_at)}`}
                                        arrived={arrived(alert.alert_id)}
                                    />
                                ))}
                            </div>
                        )}
                    </section>

                    {earlier.length > 0 && (
                        <section aria-labelledby="earlier-heading">
                            <SectionLabel id="earlier-heading">Earlier</SectionLabel>
                            <ul className="m-0 flex list-none flex-col gap-2 p-0">{earlier.map(renderEarlier)}</ul>
                        </section>
                    )}
                </>
            )}
            {acknowledgeMutation.isError && (
                <p role="alert" className="m-0 text-small text-critical-text">
                    Could not acknowledge this alert. Please try again.
                </p>
            )}
        </div>
    )
}