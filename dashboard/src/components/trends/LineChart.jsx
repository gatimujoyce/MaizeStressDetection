import { useId, useMemo, useState } from 'react'
import useWidth from './useWidth'

const HEIGHT = 190
const PAD = { top: 12, right: 12, bottom: 26, left: 42 }

function niceScale(min, max) {
    let lo = min
    let hi = max
    if (lo === hi) {
        lo -= 1
        hi += 1
    }
    const raw = (hi - lo) / 3
    const mag = 10 ** Math.floor(Math.log10(raw))
    const norm = raw / mag
    const step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag
    const from = Math.floor(lo / step) * step
    const to = Math.ceil(hi / step) * step
    const ticks = []
    for (let v = from; v <= to + step / 2; v += step) ticks.push(Number(v.toFixed(6)))
    return { lo: from, hi: to, ticks }
}

// A plain SVG line chart. points: [{ t (ms), v }], spans: [{ start, end (ms) }] are the periods an alert was open.
// A line breaks where readings stop for longer than gapMs, so a silent sensor shows as a gap and not as a straight line.
export default function LineChart({ points, spans = [], start, end, gapMs, xTicks, label, formatValue, formatMoment }) {
    const [ref, width] = useWidth()
    const [activeIndex, setActiveIndex] = useState(null)
    const hatchId = useId()

    const geometry = useMemo(() => {
        if (!width || points.length === 0) return null
        const values = points.map((p) => p.v)
        const { lo, hi, ticks } = niceScale(Math.min(...values), Math.max(...values))
        const innerW = width - PAD.left - PAD.right
        const innerH = HEIGHT - PAD.top - PAD.bottom
        const x = (t) => PAD.left + ((t - start) / (end - start)) * innerW
        const y = (v) => PAD.top + (1 - (v - lo) / (hi - lo)) * innerH
        const segments = []
        points.forEach((p, i) => {
            const prev = points[i - 1]
            if (!prev || p.t - prev.t > gapMs) segments.push([])
            segments[segments.length - 1].push({ ...p, x: x(p.t), y: y(p.v), i })
        })
        return { ticks, x, y, segments, innerW, innerH }
    }, [width, points, start, end, gapMs])

    const clampX = (value, g) => Math.min(Math.max(value, PAD.left), PAD.left + g.innerW)

    const pick = (clientX) => {
        if (!geometry) return
        const rect = ref.current.getBoundingClientRect()
        const px = clientX - rect.left
        let best = 0
        let bestDistance = Infinity
        points.forEach((p, i) => {
            const distance = Math.abs(geometry.x(p.t) - px)
            if (distance < bestDistance) {
                best = i
                bestDistance = distance
            }
        })
        setActiveIndex(best)
    }

    const onKeyDown = (event) => {
        if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
        event.preventDefault()
        setActiveIndex((current) => {
            const from = current ?? points.length - 1
            return Math.min(points.length - 1, Math.max(0, from + (event.key === 'ArrowRight' ? 1 : -1)))
        })
    }

    const active = activeIndex === null ? null : points[Math.min(activeIndex, points.length - 1)]
    const activePoint = active && geometry ? { x: geometry.x(active.t), y: geometry.y(active.v) } : null

    return (
        <div>
            <p aria-live="polite" className="m-0 mb-2 min-h-6 text-small text-ink-secondary">
                {active
                    ? `${formatMoment(active.t)}: ${formatValue(active.v)}`
                    : 'Tap or move along the chart to see a value. Arrow keys also work.'}
            </p>
            <div
                ref={ref}
                tabIndex={0}
                role="group"
                aria-label={label}
                onKeyDown={onKeyDown}
                onPointerDown={(e) => pick(e.clientX)}
                onPointerMove={(e) => pick(e.clientX)}
                onMouseLeave={() => setActiveIndex(null)}
                className="w-full touch-pan-y rounded-card outline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand"
            >
                {geometry && (
                    <svg width={width} height={HEIGHT} aria-hidden="true" className="block">
                        <defs>
                            <pattern id={hatchId} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                                <line x1="0" y1="0" x2="0" y2="6" stroke="var(--color-warning-text)" strokeWidth="1.5" opacity="0.45" />
                            </pattern>
                        </defs>
                        {spans.map((s, i) => {
                            const x1 = clampX(geometry.x(s.start), geometry)
                            const x2 = clampX(geometry.x(s.end ?? end), geometry)
                            return x2 > x1 ? (
                                <rect key={i} x={x1} y={PAD.top} width={x2 - x1} height={geometry.innerH} fill={`url(#${hatchId})`} />
                            ) : null
                        })}
                        {geometry.ticks.map((v) => (
                            <g key={v}>
                                <line x1={PAD.left} x2={PAD.left + geometry.innerW} y1={geometry.y(v)} y2={geometry.y(v)} stroke="var(--color-border)" strokeWidth="1" />
                                <text x={PAD.left - 6} y={geometry.y(v) + 4} textAnchor="end" fontSize="12" fill="var(--color-text-secondary)">
                                    {formatValue(v, true)}
                                </text>
                            </g>
                        ))}
                        {xTicks.map((tick) => (
                            <text key={tick.t} x={geometry.x(tick.t)} y={HEIGHT - 6} textAnchor="middle" fontSize="12" fill="var(--color-text-secondary)">
                                {tick.label}
                            </text>
                        ))}
                        {geometry.segments.map((seg, i) =>
                            seg.length === 1 ? (
                                <circle key={i} cx={seg[0].x} cy={seg[0].y} r="2.5" fill="var(--color-brand)" />
                            ) : (
                                <polyline
                                    key={i}
                                    points={seg.map((p) => `${p.x},${p.y}`).join(' ')}
                                    fill="none"
                                    stroke="var(--color-brand)"
                                    strokeWidth="2.5"
                                    strokeLinejoin="round"
                                    strokeLinecap="round"
                                />
                            ),
                        )}
                        {activePoint && (
                            <>
                                <line x1={activePoint.x} x2={activePoint.x} y1={PAD.top} y2={PAD.top + geometry.innerH} stroke="var(--color-text-secondary)" strokeWidth="1" strokeDasharray="3 3" />
                                <circle cx={activePoint.x} cy={activePoint.y} r="5" fill="var(--color-brand)" stroke="#fff" strokeWidth="2" />
                            </>
                        )}
                    </svg>
                )}
            </div>
        </div>
    )
}