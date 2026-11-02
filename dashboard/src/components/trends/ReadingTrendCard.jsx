import { useMemo } from 'react'
import Card, { SectionHeader } from '../ui/Card'
import LineChart from './LineChart'
import { buildTicks, formatMoment, RANGES } from './trendTime'

const FIELDS = {
    soil_moisture: { title: 'Soil moisture', unit: '%', decimals: 0, tolerance: 1.5 },
    temperature: { title: 'Temperature', unit: ' °C', decimals: 1, tolerance: 0.5 },
    humidity: { title: 'Humidity', unit: '%', decimals: 0, tolerance: 2 },
    leaf_wetness: { title: 'Leaf wetness', unit: '', decimals: 2, tolerance: 0.15 },
    nitrogen_mg_kg: { title: 'Nitrogen', unit: ' mg/kg', decimals: 0, tolerance: 2, alertClass: 'low_nitrogen' },
    phosphorus_mg_kg: { title: 'Phosphorus', unit: ' mg/kg', decimals: 0, tolerance: 1, alertClass: 'low_phosphorus' },
    potassium_mg_kg: { title: 'Potassium', unit: ' mg/kg', decimals: 0, tolerance: 5, alertClass: 'low_potassium' },
}

const number = (value, decimals) => Number(value).toFixed(decimals).replace(/\.0+$/, '')

export const FIELD_ORDER = ['soil_moisture', 'temperature', 'humidity', 'leaf_wetness']
export const NPK_FIELD_ORDER = ['nitrogen_mg_kg', 'phosphorus_mg_kg', 'potassium_mg_kg']

export function describeChange(change, field) {
    const { tolerance, decimals, unit } = FIELDS[field]
    if (change === null || change === undefined) return null
    if (Math.abs(change) < tolerance) return { arrow: '→', text: 'About the same as the day before' }
    const size = `${number(Math.abs(change), decimals)}${unit.trim() === '%' ? ' points' : unit}`
    return change > 0
        ? { arrow: '↑', text: `${size} higher than the day before` }
        : { arrow: '↓', text: `${size} lower than the day before` }
}

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
    const format = (value, axis = false) => `${number(value, axis ? Math.min(cfg.decimals, 1) : cfg.decimals)}${cfg.unit}`
    const titleId = `trend-${field}`
    const warningLevel = cfg.alertClass ? trend.nutrient_levels?.[field] : undefined

    return (
        <Card aria-labelledby={titleId}>
            <SectionHeader id={titleId} title={cfg.title} as="h3" />
            {latest === null || latest === undefined ? (
                <p className="m-0 text-body text-ink-secondary">No readings yet.</p>
            ) : (
                <>
                    <p className="m-0 text-display font-bold text-ink">{format(latest)}</p>
                    <p className="m-0 mb-3 text-small text-ink-secondary">
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
            {warningLevel !== undefined && (
                <p className="m-0 mb-3 text-small text-ink-secondary">
                    Warning level: {warningLevel} mg/kg. This level is provisional and has not been reviewed by an agronomist.
                </p>
            )}
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
                    formatValue={format}
                    formatMoment={(ms) => formatMoment(ms, rangeKey)}
                />
            )}
        </Card>
    )
}