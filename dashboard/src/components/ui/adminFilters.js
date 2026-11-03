// Helpers for the filter row on the admin panels.
export const DATE_RANGES = [
  ['all', 'Any time'],
  ['24h', 'Last 24 hours'],
  ['7d', 'Last 7 days'],
  ['30d', 'Last 30 days'],
]

const RANGE_MS = { '24h': 24 * 3600e3, '7d': 7 * 24 * 3600e3, '30d': 30 * 24 * 3600e3 }

export function inDateRange(isoTime, rangeKey, now = Date.now()) {
  if (rangeKey === 'all') return true
  const t = Date.parse(isoTime)
  return !Number.isNaN(t) && now - t <= RANGE_MS[rangeKey]
}

// Options for a FilterSelect built from the rows themselves: [['all', 'All farmers'], [id, label], ...], sorted by label.
export function uniqueOptions(rows, idOf, labelOf, allLabel) {
  const seen = new Map()
  rows.forEach((row) => {
    const id = idOf(row)
    if (id && !seen.has(id)) seen.set(id, labelOf(row))
  })
  return [['all', allLabel], ...[...seen].sort((a, b) => String(a[1]).localeCompare(String(b[1])))]
}
