import { Link } from 'react-router-dom'
import { useAcknowledgeAlertMutation, useAlerts } from '../../api/hooks'
import AttentionAlert from '../../components/AttentionAlert'
import FollowUpCard from '../../components/FollowUpCard'
import AlertRow, { AlertList } from '../../components/ui/AlertRow'
import Card, { SectionHeader } from '../../components/ui/Card'
import EmptyState from '../../components/ui/EmptyState'
import Notice from '../../components/ui/Notice'
import Page from '../../components/ui/Page'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { buttonClass, linkClass } from '../../components/ui/styles'
import useArrivals from '../../components/ui/useArrivals'
import useNow from '../../components/ui/useNow'
import { stressTitle } from '../../content/alertTitles'
import { formatWhen } from '../../content/dates'
import { useFarm } from '../../farm/FarmContext'

const byNewest = (a, b) => (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0)

export default function AlertsPage() {
    const { selectedFarmId, selectedFarm } = useFarm()
    const { data: alerts = [], isLoading, isSuccess, isError, isFetching, refetch } = useAlerts(selectedFarmId)
    const acknowledgeMutation = useAcknowledgeAlertMutation(selectedFarmId)
    const arrived = useArrivals(alerts.map((a) => a.alert_id), isSuccess)
    const now = useNow()
    const sorted = [...alerts].sort(byNewest)
    const isOngoing = (a) => a.source === 'sensor' && !a.resolved_at
    const ongoing = sorted.filter(isOngoing)
    const earlier = sorted.filter((a) => !isOngoing(a))

    const renderEarlier = (alert) => {
        const sensor = alert.source === 'sensor'
        const title = sensor
            ? `${stressTitle(alert.stress_class)}${alert.resolved_at ? ' (cleared)' : ''}`
            : `Photo check-in · ${alert.severity_label}`
        const unread = alert.status !== 'acknowledged'
        return (
            <AlertRow
                key={alert.alert_id}
                tone={alert.severity}
                className={`flex flex-wrap items-center gap-x-4 gap-y-2 !py-3 ${arrived(alert.alert_id) ? 'motion-enter' : ''}`}
            >
                <div className="min-w-0 flex-1 basis-48">
                    <p className="m-0 flex items-center gap-2 text-body font-bold text-ink">
                        {unread && (
                            <span className="inline-block h-2.5 w-2.5 shrink-0 rounded-full bg-brand">
                                <span className="sr-only">Unread:</span>
                            </span>
                        )}
                        {title}
                    </p>
                    <p className="m-0 text-small text-ink-secondary">
                        {formatWhen(alert.created_at, now)}
                        {alert.resolved_at ? ` · cleared ${formatWhen(alert.resolved_at, now)}` : ''}
                    </p>
                    {!sensor && alert.message && (
                        <p className="m-0 mt-1 text-small text-ink">{alert.message}</p>
                    )}
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                    {alert.prediction_id && (
                        <Link to={`/result/${selectedFarmId}/${alert.prediction_id}`} className={`inline-flex min-h-11 items-center text-small ${linkClass}`}>
                            View result
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
            </AlertRow>
        )
    }

    return (
        <Page>
            <PageHeader
                title="Alerts"
                subtitle={`${selectedFarm?.farm_name || 'Your field'}${ongoing.length > 0 ? ` · ${ongoing.length} need${ongoing.length === 1 ? 's' : ''} attention now` : ''}`}
            />
            <FollowUpCard />
            {isLoading ? (
                <div className="flex flex-col gap-4">
                    <Skeleton label="Loading alerts" className="h-32" />
                    <Skeleton className="h-40" />
                </div>
            ) : isError ? (
                <Notice tone="critical" onRetry={() => refetch()} retrying={isFetching}>
                    <p>Could not load alerts.</p>
                </Notice>
            ) : (
                <>
                    <section aria-labelledby="now-heading">
                        <SectionHeader id="now-heading" title="Needs attention now" />
                        {ongoing.length === 0 ? (
                            <Card>
                                <EmptyState>
                                    <p>Nothing needs your attention right now. We are watching your field and will alert you here.</p>
                                </EmptyState>
                            </Card>
                        ) : (
                            <AlertList>
                                {ongoing.map((alert) => (
                                    <AttentionAlert
                                        key={alert.alert_id}
                                        alert={alert}
                                        farmId={selectedFarmId}
                                        meta={`Ongoing · started ${formatWhen(alert.created_at, now)}`}
                                        arrived={arrived(alert.alert_id)}
                                    />
                                ))}
                            </AlertList>
                        )}
                    </section>
                    {earlier.length > 0 && (
                        <section aria-labelledby="earlier-heading">
                            <SectionHeader id="earlier-heading" title="Earlier" />
                            <AlertList>{earlier.map(renderEarlier)}</AlertList>
                        </section>
                    )}
                </>
            )}
            {acknowledgeMutation.isError && (
                <p role="alert" className="m-0 text-small text-critical-text">
                    Could not mark this alert as read. Please try again.
                </p>
            )}
        </Page>
    )
}
