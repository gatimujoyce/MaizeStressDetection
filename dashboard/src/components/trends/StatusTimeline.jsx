import { useId, useMemo, useState } from 'react'
import { buildTicks, formatMoment } from './trendTime'
import useWidth from './useWidth'

const LANE_H = 52
const TRACK_H = 26
const AXIS_H = 24
const PAD_X = 10

const SENSOR_NAMES = {
    normal: 'Normal',
    heat_stress: 'Heat stress',
    drought_stress: 'Drought stress',
    waterlogging_risk: 'Waterlogging risk',
}
const SHORT_NAMES = { normal: 'Normal', heat_stress: 'Heat', drought_stress: 'Drought', waterlogging_risk: 'Waterlogging' }
const TONES = {
    healthy: { fill: 'var(--color-healthy-bg)', stroke: 'var(--color-healthy-text)', glyph: '✓' },
    warning: { fill: 'var(--color-warning-bg)', stroke: 'var(--color-warning-text)', glyph: '!' },
    critical: { fill: 'var(--color-critical-bg)', stroke: 'var(--color-critical-text)', glyph: '!' },
    neutral: { fill: 'var(--color-neutral-bg)', stroke: 'var(--color-neutral-text)', glyph: '?' },
}
const SEVERITY = { healthy: 0, neutral: 1, warning: 2, critical: 3 }
const MARKER_GAP = 26 // check-ins closer than this many pixels become one marker
const sensorTone = (status) => (status === 'normal' ? 'healthy' : status === 'waterlogging_risk' ? 'critical' : 'warning')

// Three rows, one per branch of the system, on one shared time axis:
//   Sensor model: what the model said for each period (stretches).
//   Disease and Nutrient: what the leaf photo said at each check-in (markers).
// Every status is a word or a symbol as well as a colour, and the same facts are available as a list.
export default function StatusTimeline({ rangeKey, start, end, sensor, checkins }) {
    const [ref, width] = useWidth()
    const [picked, setPicked] = useState(null)
    const hatchId = useId()

    const model = useMemo(() => {
        const stretches = (sensor.segments || []).map((s) => ({ ...s, from: Date.parse(s.start), to: Date.parse(s.end) }))
        const inRange = checkins.filter((c) => c.at >= start && c.at <= end).sort((a, b) => a.at - b.at)
        return { stretches, inRange }
    }, [sensor.segments, checkins, start, end])

    const innerW = Math.max(width - PAD_X * 2, 1)
    const x = (t) => PAD_X + ((Math.min(Math.max(t, start), end) - start) / (end - start)) * innerW
    const ticks = useMemo(() => buildTicks(rangeKey, start, end), [rangeKey, start, end])
    const height = LANE_H * 3 + AXIS_H
    const laneTop = (lane) => lane * LANE_H + 20

    const rows = useMemo(() => {
        const list = []
        model.stretches.forEach((s) =>
            list.push({ lane: 'Sensor model', at: s.from, to: s.to, text: SENSOR_NAMES[s.status] || 'Normal', tone: sensorTone(s.status) }),
        )
        model.inRange.forEach((c) => {
            list.push({ lane: 'Disease', at: c.at, text: c.disease.label, tone: c.disease.tone })
            list.push({ lane: 'Nutrient', at: c.at, text: c.nutrient.label, detail: c.nutrient.detail, tone: c.nutrient.tone })
        })
        return list.sort((a, b) => a.at - b.at)
    }, [model])

    // Check-ins taken close together would sit on top of each other, so they are grouped into one marker that shows the
    // most serious status among them and a count. Tapping it lists everything inside.
    const clusters = useMemo(() => {
        if (width === 0) return []
        const groups = []
        model.inRange.forEach((c) => {
            const px = x(c.at)
            const last = groups[groups.length - 1]
            if (last && px - last.lastPx < MARKER_GAP) {
                last.items.push(c)
                last.lastPx = px
            } else {
                groups.push({ items: [c], firstPx: px, lastPx: px })
            }
        })
        const worst = (items, key) => items.reduce((a, b) => (SEVERITY[b[key].tone] > SEVERITY[a[key].tone] ? b : a))
        return groups.map((g) => ({
            items: g.items,
            px: (g.firstPx + g.lastPx) / 2,
            first: g.items[0].at,
            last: g.items[g.items.length - 1].at,
            disease: worst(g.items, 'disease').disease,
            nutrient: worst(g.items, 'nutrient').nutrient,
        }))
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [model.inRange, width, start, end])

    const describeCluster = (cluster, lane) => {
        const key = lane === 'Disease' ? 'disease' : 'nutrient'
        if (cluster.items.length === 1) {
            const only = cluster.items[0][key]
            return { lane, at: cluster.first, text: only.label, detail: only.detail }
        }
        return {
            lane,
            at: cluster.first,
            to: cluster.last,
            text: `${cluster.items.length} check-ins: ${cluster.items.map((c) => c[key].label).join('; ')}`,
        }
    }

    const pick = (event) => {
        const rect = ref.current.getBoundingClientRect()
        const px = event.clientX - rect.left
        const lane = Math.floor((event.clientY - rect.top) / LANE_H)
        const t = start + ((px - PAD_X) / innerW) * (end - start)
        if (lane === 0) {
            const hit = rows.find((r) => r.lane === 'Sensor model' && t >= r.at && t <= r.to)
            setPicked(hit || null)
        } else if (lane === 1 || lane === 2) {
            const name = lane === 1 ? 'Disease' : 'Nutrient'
            let best = null
            let bestDistance = 28
            clusters.forEach((c) => {
                const distance = Math.abs(c.px - px)
                if (distance < bestDistance) {
                    best = describeCluster(c, name)
                    bestDistance = distance
                }
            })
            setPicked(best)
        }
    }

    const readout = picked
        ? `${picked.lane}: ${picked.text}${picked.detail ? '. ' + picked.detail : ''}, ${formatMoment(picked.at, rangeKey)}${picked.to ? ' to ' + formatMoment(picked.to, rangeKey) : ''}`
        : 'Tap a stretch or a marker to see what it says.'

    return (
        <div>
            <p aria-live="polite" className="m-0 mb-2 min-h-6 text-small text-ink-secondary">{readout}</p>
            <div ref={ref} className="w-full" onPointerDown={pick} onPointerMove={(e) => e.pointerType === 'mouse' && pick(e)}>
                {width > 0 && (
                    <svg width={width} height={height} aria-hidden="true" className="block">
                        <defs>
                            <pattern id={hatchId} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                                <line x1="0" y1="0" x2="0" y2="6" stroke="var(--color-warning-text)" strokeWidth="1.5" opacity="0.45" />
                            </pattern>
                        </defs>
                        {['Sensor model', 'Disease (leaf photo)', 'Nutrient (leaf photo)'].map((name, lane) => (
                            <g key={name}>
                                <text x={PAD_X} y={laneTop(lane) - 6} fontSize="12" fontWeight="700" fill="var(--color-text-secondary)">{name}</text>
                                <rect x={PAD_X} y={laneTop(lane)} width={innerW} height={TRACK_H} rx="6" fill="var(--color-bg)" stroke="var(--color-border)" />
                            </g>
                        ))}
                        {ticks.map((tick) => (
                            <g key={tick.t}>
                                <line x1={x(tick.t)} x2={x(tick.t)} y1={laneTop(0)} y2={laneTop(2) + TRACK_H} stroke="var(--color-border)" strokeDasharray="2 4" />
                                <text x={x(tick.t)} y={height - 6} textAnchor="middle" fontSize="12" fill="var(--color-text-secondary)">{tick.label}</text>
                            </g>
                        ))}
                        {model.stretches.map((s, i) => {
                            const tone = TONES[sensorTone(s.status)]
                            const x1 = x(s.from)
                            const w = Math.max(x(s.to) - x1, 6)
                            return (
                                <g key={i}>
                                    <rect x={x1} y={laneTop(0)} width={w} height={TRACK_H} rx="6" fill={tone.fill} stroke={tone.stroke} />
                                    {s.status !== 'normal' && <rect x={x1} y={laneTop(0)} width={w} height={TRACK_H} rx="6" fill={`url(#${hatchId})`} />}
                                    {w > 78 && (
                                        <text x={x1 + w / 2} y={laneTop(0) + 17} textAnchor="middle" fontSize="12" fontWeight="700" fill={tone.stroke}>
                                            {SHORT_NAMES[s.status] || 'Normal'}
                                        </text>
                                    )}
                                </g>
                            )
                        })}
                        {clusters.map((c, i) =>
                            [['disease', 1], ['nutrient', 2]].map(([key, lane]) => {
                                const tone = TONES[c[key].tone] || TONES.neutral
                                const cy = laneTop(lane) + TRACK_H / 2
                                const many = c.items.length > 1
                                return (
                                    <g key={`${key}-${i}`}>
                                        <circle cx={c.px} cy={cy} r="11" fill={tone.fill} stroke={tone.stroke} strokeWidth="2" />
                                        <text x={c.px} y={cy + 4.5} textAnchor="middle" fontSize="13" fontWeight="700" fill={tone.stroke}>{tone.glyph}</text>
                                        {many && (
                                            <g>
                                                <circle cx={c.px + 10} cy={cy - 10} r="8" fill="var(--color-text-primary)" />
                                                <text x={c.px + 10} y={cy - 6.5} textAnchor="middle" fontSize="11" fontWeight="700" fill="#fff">{c.items.length}</text>
                                            </g>
                                        )}
                                    </g>
                                )
                            }),
                        )}
                    </svg>
                )}
            </div>
            <p className="m-0 mt-2 text-small text-ink-secondary">
                ✓ looks fine · ! possible or flagged · ? not sure or photo unclear. A number means several check-ins close together; tap it to see them. Hatched stretches are heat, drought or waterlogging.
            </p>
            {!sensor.available && (
                <p className="m-0 mt-1 text-small text-ink-secondary">The sensor model is not running right now, so its row is empty.</p>
            )}
            <details className="mt-3">
                <summary className="min-h-11 cursor-pointer py-2 text-small font-bold text-ink">Show these as a list</summary>
                {rows.length === 0 ? (
                    <p className="m-0 text-small text-ink-secondary">Nothing to show in this period yet.</p>
                ) : (
                    <ul className="m-0 flex list-none flex-col gap-2 p-0">
                        {rows.map((r, i) => (
                            <li key={i} className="text-small text-ink">
                                <strong>{r.lane}:</strong> {r.text}
                                {r.detail ? `. ${r.detail}` : ''}
                                <span className="text-ink-secondary"> · {formatMoment(r.at, rangeKey)}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </details>
        </div>
    )
}