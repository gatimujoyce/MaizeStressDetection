import { useMemo } from 'react'
import Card, { SectionHeader } from '../ui/Card'
import LineChart from './LineChart'
import { describeChange, FIELDS, formatNumber } from './trendFields'
import { buildTicks, formatMoment, RANGES } from './trendTime'

// One reading over the chosen range: the latest value, how it moved since the day before, and the chart.
export default function ReadingTrendCard({ field, trend, rangeKey }) {
    const cfg = FIELDS[field]
    const range = RANGES.find((r) => r.key === rangeKey)
    const start = Date.parse(trend.from)
    const end = Date.parse(trend.to)
    const gapMs = trend.bucket_minutes * 60e3 * 2.5
    const points = useMemo(
        () => trend.points.filter((p) => p[field] !== null && p[field] !== undefined).map((p) => ({ t: Date.parse(p.t), v: p[field] })),
        [trend.points, field],
    )
    // Low-nutrient alerts shade only their own nutrient's chart; the sensor-model alerts shade the four sensor charts.
    const spans = useMemo(() => {
        const alerts = cfg.alertClass
            ? (trend.nutrient_alerts ?? []).filter((a) => a.stress_class === cfg.alertClass)
            : trend.alerts
        return alerts.map((a) => ({ start: Date.parse(a.start), end: a.end ? Date.parse(a.end) : null }))
    }, [trend.alerts, trend.nutrient_alerts, cfg.alertClass])
    const xTicks = useMemo(() => buildTicks(rangeKey, start, end), [rangeKey, start, end])
    const latest = trend.summary[field].latest
    const change = describeChange(trend.summary[field].change, field)
    const format = (value) => `${formatNumber(value, cfg.decimals)}${cfg.unit}`
    const formatTick = (value) => formatNumber(value, Math.min(cfg.decimals, 1))
    const titleId = `trend-${field}`
    const warningLevel = cfg.alertClass ? trend.nutrient_levels?.[field] : undefined

    return (
        <Card aria-labelledby={titleId} className="flex flex-col">
            <SectionHeader id={titleId} title={cfg.title} as="h3" className="!mb-2" />
            {latest === null || latest === undefined ? (
                <p className="m-0 mb-3 text-body text-ink-secondary">No readings yet.</p>
            ) : (
                <>
                    <p className="m-0 text-figure tabular-nums text-ink">{format(latest)}</p>
                    <p className="m-0 mb-3 mt-1 text-small text-ink-secondary">
                        {change ? (
                            <>
                                <span aria-hidden="true">{change.arrow} </span>
                                {change.text}
                            </>
                        ) : (
                            'Not enough readings yet to compare with the day before'
                        )}
                    </p>
                </>
            )}
            {cfg.note && <p className="m-0 mb-3 text-small text-ink-secondary">{cfg.note}</p>}
            {warningLevel !== undefined && (
                <p className="m-0 mb-3 text-small text-ink-secondary">
                    Warning level: {warningLevel} mg/kg. This level is provisional and has not been reviewed by an agronomist.
                </p>
            )}
            <div className="mt-auto">
                {points.length === 0 ? (
                    <p className="m-0 text-small text-ink-secondary">
                        No readings in the last {range.label}.
                    </p>
                ) : (
                    <LineChart
                        points={points}
                        spans={spans}
                        start={start}
                        end={end}
                        gapMs={gapMs}
                        xTicks={xTicks}
                        label={`${cfg.title}, last ${range.label}`}
                        axisUnit={cfg.unit.trim()}
                        formatValue={format}
                        formatTick={formatTick}
                        formatMoment={(ms) => formatMoment(ms, rangeKey)}
                    />
                )}
            </div>
        </Card>
    )
}
