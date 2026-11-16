import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useFarmHistory, useReadingTrend } from '../../api/hooks'
import { CheckIcon, WarningIcon } from '../../components/Icons'
import TrendChart from '../../components/TrendChart'
import ReadingTrendCard from '../../components/trends/ReadingTrendCard'
import StatusTimeline from '../../components/trends/StatusTimeline'
import { FIELD_ORDER, NPK_FIELD_ORDER } from '../../components/trends/trendFields'
import { RANGES } from '../../components/trends/trendTime'
import Card, { SectionHeader } from '../../components/ui/Card'
import EmptyState from '../../components/ui/EmptyState'
import Notice from '../../components/ui/Notice'
import Page from '../../components/ui/Page'
import PageHeader from '../../components/ui/PageHeader'
import Segmented from '../../components/ui/Segmented'
import Skeleton from '../../components/ui/Skeleton'
import GrowthStageCard from '../../components/GrowthStageCard'
import { stressTitle } from '../../content/alertTitles'
import { useFarm } from '../../farm/FarmContext'

const STALE_HOURS = 3

function Overview({ trend, rangeLabel }) {
    const everything = [...trend.alerts, ...(trend.nutrient_alerts ?? [])]
    const open = everything.filter((a) => !a.end)
    const past = everything.filter((a) => a.end)
    const when = (iso) => new Date(iso).toLocaleString('en-KE', { weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })

    return (
        <Card aria-labelledby="overview-title">
            <SectionHeader id="overview-title" title="Anything unusual?" />
            {open.length > 0 ? (
                <ul className="m-0 flex list-none flex-col gap-2 p-0">
                    {open.map((a) => (
                        <li key={a.id} className="flex items-start gap-2 text-body font-bold text-warning-text">
                            <span aria-hidden="true" className="mt-1 flex shrink-0"><WarningIcon size={18} /></span>
                            <span>
                                {stressTitle(a.stress_class)}, ongoing since {when(a.start)}. See the Alerts tab.
                            </span>
                        </li>
                    ))}
                </ul>
            ) : (
                <p className="m-0 flex items-start gap-2 text-body text-ink">
                    <span aria-hidden="true" className="mt-1 flex shrink-0 text-healthy-text"><CheckIcon size={18} /></span>
                    <span>No alert is open for your plot right now.</span>
                </p>
            )}
            {past.length > 0 && (
                <p className="m-0 mt-3 text-small text-ink-secondary">
                    Shaded stripes on the charts show when an alert was open in the last {rangeLabel}:{' '}
                    {past.length + open.length === 1 ? '1 alert' : `${past.length + open.length} alerts`}.
                </p>
            )}
            {past.length === 0 && open.length > 0 && (
                <p className="m-0 mt-3 text-small text-ink-secondary">Shaded stripes on the charts show when the alert was open.</p>
            )}
        </Card>
    )
}

export default function TrendsPage() {
    const { selectedFarmId, selectedFarm } = useFarm()
    const { hash } = useLocation()
    const [rangeKey, setRangeKey] = useState('7d')
    const range = RANGES.find((r) => r.key === rangeKey)
    const { data: trend, isLoading, isError, isFetching, refetch } = useReadingTrend(selectedFarmId, rangeKey)
    const history = useFarmHistory(selectedFarmId)
    const hasReadings = trend && trend.latest_at
    const stale = hasReadings && trend.hours_since_latest >= STALE_HOURS
    const thin = hasReadings && trend.hours_of_data < range.ms / 3600e3 / 2
    const hasNpkSensor = Boolean(selectedFarm?.hasNpkSensor)

    // "Past photo checks" on Home links here; scroll to the list once the charts above it have their height.
    useEffect(() => {
        if (hash !== '#photo-checks' || isLoading || history.isLoading) return
        document.getElementById('photo-checks')?.scrollIntoView({ block: 'start' })
    }, [hash, isLoading, history.isLoading])

    return (
        <Page>
            <PageHeader
                title="Field trends"
                subtitle={
                    <>
                        <p className="m-0">{selectedFarm?.farm_name || 'Your field'}</p>
                        <GrowthStageCard />
                    </>
                }
            />
            <Segmented
                label="Time range"
                options={RANGES.map((r) => ({ key: r.key, label: r.label }))}
                value={rangeKey}
                onChange={setRangeKey}
                block
            />
            {isLoading ? (
                <div className="flex flex-col gap-4">
                    <Skeleton label="Loading trends" className="h-24" />
                    <Skeleton className="h-64" />
                    <Skeleton className="h-64" />
                </div>
            ) : isError ? (
                <Notice tone="critical" onRetry={() => refetch()} retrying={isFetching}>
                    <p>Could not load your field trends.</p>
                </Notice>
            ) : !hasReadings ? (
                <Card>
                    <EmptyState title="No sensor readings yet">
                        <p>Trends will appear here once your sensors start reporting.</p>
                    </EmptyState>
                </Card>
            ) : (
                <>
                    {(stale || thin) && (
                        <div className="flex flex-col gap-3">
                            {stale && (
                                <Notice tone="warning">
                                    <p>
                                        No new readings for {Math.round(trend.hours_since_latest)} hours. The charts show the last readings we received.
                                    </p>
                                </Notice>
                            )}
                            {thin && (
                                <Notice tone="neutral">
                                    <p>We only have {Math.round(trend.hours_of_data)} hours of readings in this period so far, so the charts are short.</p>
                                </Notice>
                            )}
                        </div>
                    )}
                    <Overview trend={trend} rangeLabel={range.label} />
                    <Card aria-labelledby="status-title">
                        <SectionHeader id="status-title" title="Status over time" />
                        <StatusTimeline
                            rangeKey={rangeKey}
                            start={Date.parse(trend.from)}
                            end={Date.parse(trend.to)}
                            sensor={trend.sensor_status}
                            checkins={history.data ?? []}
                        />
                    </Card>
                    <section aria-labelledby="readings-title">
                        <SectionHeader id="readings-title" title="Sensor readings" />
                        <div className="grid gap-4 md:grid-cols-2">
                            {FIELD_ORDER.map((field) => (
                                <ReadingTrendCard key={field} field={field} trend={trend} rangeKey={rangeKey} />
                            ))}
                        </div>
                    </section>
                </>
            )}
            {(trend?.has_npk_sensor && hasReadings) ? (
                <section aria-labelledby="npk-title">
                    <SectionHeader id="npk-title" title="Soil nutrients (NPK sensor)" />
                    <div className="grid gap-4 md:grid-cols-2">
                        {NPK_FIELD_ORDER.map((field) => (
                            <ReadingTrendCard key={field} field={field} trend={trend} rangeKey={rangeKey} />
                        ))}
                    </div>
                </section>
            ) : selectedFarm && !hasNpkSensor && (
                <section aria-labelledby="npk-off-title">
                    <SectionHeader
                        id="npk-off-title"
                        title="Soil nutrient sensor"
                        description="No NPK sensor is set up for this plot. To add one, contact your administrator."
                        className="!mb-0"
                    />
                </section>
            )}
            <TrendChart
                history={history.data ?? []}
                isLoading={history.isLoading}
                isError={history.isError}
                onRetry={() => history.refetch()}
                retrying={history.isFetching}
            />
        </Page>
    )
}
