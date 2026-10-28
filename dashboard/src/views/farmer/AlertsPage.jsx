import { Link } from 'react-router-dom'
import { useAcknowledgeAlertMutation, useAlerts } from '../../api/hooks'
import { WarningIcon, ErrorIcon } from '../../components/Icons'
import { useFarm } from '../../farm/FarmContext'

const STRESS_TITLES = {
    heat_stress: 'Heat stress',
    drought_stress: 'Drought stress',
    waterlogging_risk: 'Waterlogging risk',
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

function adviceOf(alert) {
    if (!alert.message) return ''
    return alert.message.includes(': ') ? alert.message.split(': ').slice(1).join(': ') : alert.message
}

function Stripe({ critical }) {
    return (
        <span
            aria-hidden="true"
            className="absolute left-0 top-0 h-full w-1.5 rounded-l-sm"
            style={{ background: critical ? 'var(--color-critical-text)' : 'var(--color-warning-text)' }}
        />
    )
}

export default function AlertsPage() {
    const { selectedFarmId, selectedFarm } = useFarm()
    const { data: alerts = [], isLoading, isError, isFetching, refetch } = useAlerts(selectedFarmId)
    const acknowledgeMutation = useAcknowledgeAlertMutation(selectedFarmId)

    const sorted = [...alerts].sort(byNewest)
    const isOngoing = (a) => a.source === 'sensor' && !a.resolved_at
    const ongoing = sorted.filter(isOngoing)
    const earlier = sorted.filter((a) => !isOngoing(a))

    const markRead = (alert) =>
        alert.status === 'acknowledged' ? null : (
            <button
                type="button"
                onClick={() => acknowledgeMutation.mutate(alert.alert_id)}
                disabled={acknowledgeMutation.isPending}
                className="min-h-11 text-sm font-semibold text-[var(--color-brand)] underline-offset-2 hover:underline disabled:opacity-60"
            >
                Mark as read
            </button>
        )

    const renderOngoing = (alert) => {
        const critical = alert.severity === 'critical'
        const Icon = critical ? ErrorIcon : WarningIcon
        return (
            <article
                key={alert.alert_id}
                className={`relative overflow-hidden rounded-sm border border-[var(--color-border)] py-4 pl-6 pr-4 ${critical ? 'bg-[var(--color-critical-bg)]' : 'bg-[var(--color-warning-bg)]'}`}
            >
                <Stripe critical={critical} />
                <div className={`flex items-center gap-2 ${critical ? 'text-[var(--color-critical-text)]' : 'text-[var(--color-warning-text)]'}`}>
                    <Icon size={16} />
                    <h3 className="m-0 text-base font-bold">{STRESS_TITLES[alert.stress_class] || 'Field alert'}</h3>
                    <span className="ml-auto rounded-full border border-current px-2 py-0.5 text-xs font-semibold">
                        {critical ? 'Urgent' : 'Act soon'}
                    </span>
                </div>
                <p className="mb-0 mt-2 text-[15px] leading-snug text-[var(--color-text-primary)]">{adviceOf(alert)}</p>
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs text-[var(--color-text-secondary)]">Ongoing · started {formatWhen(alert.created_at)}</span>
                    {markRead(alert)}
                </div>
            </article>
        )
    }

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
                className="relative flex flex-wrap items-center gap-x-3 gap-y-1 overflow-hidden rounded-sm border border-[var(--color-border)] bg-[var(--color-surface,transparent)] py-3 pl-6 pr-4"
            >
                <Stripe critical={critical} />
                <div className="min-w-0 flex-1">
                    <p className="m-0 flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)]">
                        {unread && <span aria-label="Unread" className="inline-block h-2 w-2 rounded-full bg-[var(--color-brand)]" />}
                        {title}
                    </p>
                    <p className="m-0 text-xs text-[var(--color-text-secondary)]">
                        {formatWhen(alert.created_at)}
                        {alert.resolved_at ? ` · cleared ${formatWhen(alert.resolved_at)}` : ''}
                    </p>
                </div>
                {alert.prediction_id && (
                    <Link to={`/result/${selectedFarmId}/${alert.prediction_id}`} className="text-sm font-semibold text-[var(--color-brand)] underline-offset-2 hover:underline">
                        View result →
                    </Link>
                )}
                {markRead(alert)}
            </li>
        )
    }

    return (
        <div className="mx-auto max-w-2xl px-4 py-8">
            <header className="mb-6">
                <h1 className="m-0 text-2xl font-bold text-[var(--color-text-primary)]">Alerts</h1>
                <p className="mb-0 mt-1 text-[15px] text-[var(--color-text-secondary)]">
                    {selectedFarm?.farm_name || 'Your field'}
                    {ongoing.length > 0 ? ` · ${ongoing.length} need${ongoing.length === 1 ? 's' : ''} attention now` : ''}
                </p>
            </header>

            {isLoading ? (
                <p className="text-sm text-[var(--color-text-secondary)]">Loading alerts…</p>
            ) : isError ? (
                <div role="alert" className="text-sm text-[var(--color-critical-text)]">
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
            ) : (
                <>
                    <section aria-labelledby="now-heading" className="mb-8">
                        <h2 id="now-heading" className="mb-3 mt-0 text-sm font-semibold uppercase tracking-wide text-[var(--color-text-secondary)]">
                            Needs attention now
                        </h2>
                        {ongoing.length === 0 ? (
                            <p className="m-0 rounded-sm border border-[var(--color-border)] p-4 text-[15px] text-[var(--color-text-primary)]">
                                Nothing needs your attention right now. We are watching your field and will alert you here.
                            </p>
                        ) : (
                            <div className="flex flex-col gap-3">{ongoing.map(renderOngoing)}</div>
                        )}
                    </section>

                    {earlier.length > 0 && (
                        <section aria-labelledby="earlier-heading">
                            <h2 id="earlier-heading" className="mb-3 mt-0 text-sm font-semibold uppercase tracking-wide text-[var(--color-text-secondary)]">
                                Earlier
                            </h2>
                            <ul className="m-0 flex list-none flex-col gap-2 p-0">{earlier.map(renderEarlier)}</ul>
                        </section>
                    )}
                </>
            )}
            {acknowledgeMutation.isError && (
                <p role="alert" className="mt-3 text-sm text-[var(--color-critical-text)]">
                    Could not acknowledge this alert. Please try again.
                </p>
            )}
        </div>
    )
}