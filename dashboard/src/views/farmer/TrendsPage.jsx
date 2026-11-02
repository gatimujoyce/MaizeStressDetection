import { useState } from 'react'
import { useFarmHistory, useReadingTrend } from '../../api/hooks'
import { CheckIcon, WarningIcon } from '../../components/Icons'
import TrendChart from '../../components/TrendChart'
import NpkSetting from '../../components/trends/NpkSetting'
import ReadingTrendCard, { FIELD_ORDER, NPK_FIELD_ORDER } from '../../components/trends/ReadingTrendCard'
import StatusTimeline from '../../components/trends/StatusTimeline'
import { RANGES } from '../../components/trends/trendTime'
import Card, { SectionHeader } from '../../components/ui/Card'
import Notice from '../../components/ui/Notice'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { useFarm } from '../../farm/FarmContext'

const STRESS_TITLES = {
    heat_stress: 'Heat stress',
    drought_stress: 'Drought stress',
    waterlogging_risk: 'Waterlogging risk',
    low_nitrogen: 'Low nitrogen',
    low_phosphorus: 'Low phosphorus',
    low_potassium: 'Low potassium',
}
const STALE_HOURS = 3

function RangeTabs({ value, onChange }) {
    return (
        <div role="radiogroup" aria-label="Time range" className="flex gap-2">
            {RANGES.map((range) => {
                const selected = range.key === value
                return (
                    <button
                        key={range.key}
                        type="button"
                        role="radio"
                        aria-checked={selected}
                        onClick={() => onChange(range.key)}
                        className={`min-h-11 flex-1 rounded-card border px-3 text-body font-bold ${
                            selected ? 'border-brand bg-brand text-white' : 'border-border bg-surface text-ink'
                        }`}
                    >
                        {range.label}
                    </button>
                )
            })}
        </div>
    )
}

function Overview({ trend, rangeLabel }) {
    const everything = [...trend.alerts, ...(trend.nutrient_alerts ?? [])]
    const open = everything.filter((a) => !a.end)
    const past = everything.filter((a) => a.end)
    const titleOf = (a) => STRESS_TITLES[a.stress_class] || 'Field alert'
    const when = (iso) => new Date(iso).toLocaleString('en-KE', { weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })

    return (
        <Card aria-labelledby="overview-title">
            <SectionHeader id="overview-title" title="Anything unusual?" as="h2" />
            {open.length > 0 ? (
                <ul className="m-0 flex list-none flex-col gap-2 p-0">
                    {open.map((a) => (
                        <li key={a.id} className="flex items-start gap-2 text-body font-bold text-warning-text">
                            <WarningIcon size={20} />
                            <span>
                                {titleOf(a)}, ongoing since {when(a.start)}. See the Alerts tab.
                            </span>
                        </li>
                    ))}
                </ul>
            ) : (
                <p className="m-0 flex items-start gap-2 text-body text-ink">
                    <span className="text-healthy-text"><CheckIcon size={20} /></span>
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
    const [rangeKey, setRangeKey] = useState('7d')
    const rangeLabel = RANGES.find((r) => r.key === rangeKey).label
    const { data: trend, isLoading, isError, isFetching, refetch } = useReadingTrend(selectedFarmId, rangeKey)
    const { data: history = [] } = useFarmHistory(selectedFarmId)

    const hasReadings = trend && trend.latest_at
    const stale = hasReadings && trend.hours_since_latest >= STALE_HOURS
    const thin = hasReadings && trend.hours_of_data < RANGES.find((r) => r.key === rangeKey).ms / 3600e3 / 2

    return (
        <div className="mx-auto flex max-w-4xl flex-col gap-6">
            <PageHeader title="Field Trends" subtitle={`Plot: ${selectedFarm?.farm_name || 'Your field'}`} />
            <RangeTabs value={rangeKey} onChange={setRangeKey} />

            {isLoading ? (
                <div className="flex flex-col gap-3">
                    <Skeleton label="Loading trends…" className="h-24" />
                    <Skeleton className="h-64" />
                    <Skeleton className="h-64" />
                </div>
            ) : isError ? (
                <Notice tone="critical" onRetry={() => refetch()} retrying={isFetching}>
                    <p>Could not load your field trends.</p>
                </Notice>
            ) : !hasReadings ? (
                <Notice tone="info">
                    <p>No sensor readings yet. Trends will appear here once your sensors start reporting.</p>
                </Notice>
            ) : (
                <>
                    {stale && (
                        <Notice tone="warning">
                            <p>
                                No new readings for {Math.round(trend.hours_since_latest)} hours. The charts show the last readings we received.
                            </p>
                        </Notice>
                    )}
                    {thin && (
                        <Notice tone="info">
                            <p>We only have {Math.round(trend.hours_of_data)} hours of readings in this period so far, so the charts are short.</p>
                        </Notice>
                    )}
                    <Overview trend={trend} rangeLabel={rangeLabel} />
                    <Card aria-labelledby="status-title">
                        <SectionHeader id="status-title" title="Status over time" as="h2" />
                        <StatusTimeline
                            rangeKey={rangeKey}
                            start={Date.parse(trend.from)}
                            end={Date.parse(trend.to)}
                            sensor={trend.sensor_status}
                            checkins={history}
                        />
                    </Card>
                    <div className="grid gap-4 md:grid-cols-2">
                        {FIELD_ORDER.map((field) => (
                            <ReadingTrendCard key={field} field={field} trend={trend} rangeKey={rangeKey} />
                        ))}
                    </div>
                    {trend.has_npk_sensor && (
                        <section aria-labelledby="npk-title" className="flex flex-col gap-3">
                            <h2 id="npk-title" className="m-0 text-heading">Soil nutrients (NPK sensor)</h2>
                            <div className="grid gap-4 md:grid-cols-2">
                                {NPK_FIELD_ORDER.map((field) => (
                                    <ReadingTrendCard key={field} field={field} trend={trend} rangeKey={rangeKey} />
                                ))}
                            </div>
                        </section>
                    )}
                </>
            )}

            <NpkSetting farm={selectedFarm} />
            <TrendChart history={history} />
        </div>
    )
}