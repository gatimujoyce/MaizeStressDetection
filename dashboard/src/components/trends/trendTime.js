const HOUR = 3600e3
const DAY = 24 * HOUR

export const RANGES = [
    { key: '24h', label: '24 hours', ms: DAY },
    { key: '7d', label: '7 days', ms: 7 * DAY },
    { key: '30d', label: '30 days', ms: 30 * DAY },
]

// Axis labels at local times: every 6 hours for a day, every day for a week, every 5 days for a month.
export function buildTicks(rangeKey, startMs, endMs) {
    const ticks = []
    if (rangeKey === '24h') {
        const d = new Date(startMs)
        d.setMinutes(0, 0, 0)
        while (d.getTime() < startMs || d.getHours() % 6 !== 0) d.setHours(d.getHours() + 1)
        for (; d.getTime() <= endMs; d.setHours(d.getHours() + 6)) {
            ticks.push({ t: d.getTime(), label: d.toLocaleTimeString('en-KE', { hour: 'numeric' }) })
        }
        return ticks
    }
    const step = rangeKey === '7d' ? 1 : 5
    const d = new Date(startMs)
    d.setHours(0, 0, 0, 0)
    if (d.getTime() < startMs) d.setDate(d.getDate() + 1)
    for (; d.getTime() <= endMs; d.setDate(d.getDate() + step)) {
        ticks.push({
            t: d.getTime(),
            label: rangeKey === '7d'
                ? d.toLocaleDateString('en-KE', { weekday: 'short' })
                : d.toLocaleDateString('en-KE', { day: 'numeric', month: 'short' }),
        })
    }
    return ticks
}

export function formatMoment(ms, rangeKey) {
    const opts = rangeKey === '24h'
        ? { weekday: 'short', hour: 'numeric', minute: '2-digit' }
        : { weekday: 'short', day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }
    return new Date(ms).toLocaleString('en-KE', opts)
}