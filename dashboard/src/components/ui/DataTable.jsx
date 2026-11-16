import { useState } from 'react'
import { focusRing } from './styles'

function compare(a, b) {
  if (a == null && b == null) return 0
  if (a == null) return 1
  if (b == null) return -1
  if (typeof a === 'number' && typeof b === 'number') return a - b
  return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' })
}

function SortArrow({ dir }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 12 12" className={`h-3 w-3 shrink-0 ${dir ? 'opacity-100' : 'opacity-40'}`} fill="currentColor">
      {dir !== 'desc' && <path d="M6 1.5 9.5 5h-7z" />}
      {dir !== 'asc' && <path d="M6 10.5 2.5 7h7z" />}
    </svg>
  )
}

// Dense admin table: the header stays visible while the body scrolls, sortable columns announce their state with
// aria-sort, numbers right-align in tabular figures. On narrow screens the table scrolls inside its own box,
// never the page.
//   columns   [{ key, label, render(row), sortValue?(row), align?: 'right', className?, hideBelowSm? }]
//             hideBelowSm: the column is left out under 640px (show its value inside another cell there instead)
//   flush     inside a flush Card: no border or rounding of its own (the card provides them)
//   wide      false for a short table (few columns) that should not force a minimum width
export default function DataTable({ caption, columns, rows, rowKey, initialSort, empty, maxHeight = 'max-h-[70vh]', flush = false, wide = true }) {
  const [sort, setSort] = useState(initialSort ?? null)
  const sortColumn = columns.find((column) => column.key === sort?.key)
  const sorted = sortColumn?.sortValue
    ? [...rows].sort((a, b) => compare(sortColumn.sortValue(a), sortColumn.sortValue(b)) * (sort.dir === 'desc' ? -1 : 1))
    : rows

  const toggle = (key) =>
    setSort((current) => (current?.key === key ? { key, dir: current.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }))

  if (rows.length === 0) {
    return <p className={`m-0 text-small text-ink-secondary ${flush ? 'border-t border-border px-4 py-6 sm:px-6' : 'py-2'}`}>{empty}</p>
  }

  const edge = (index) => (flush ? (index === 0 ? 'pl-4 sm:pl-6' : '') + (index === columns.length - 1 ? ' pr-4 sm:pr-6' : '') : '')

  // relative: anything absolutely placed inside (screen-reader text in a row button) stays inside this scroll box.
  return (
    <div className={`relative overflow-auto ${flush ? 'border-t border-border' : 'rounded-control border border-border'} ${maxHeight}`}>
      <table className={`w-full border-collapse text-left text-small ${wide ? 'min-w-table' : ''}`}>
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            {columns.map((column, index) => {
              const dir = sort?.key === column.key ? sort.dir : null
              return (
                <th
                  key={column.key}
                  scope="col"
                  aria-sort={column.sortValue ? (dir === 'asc' ? 'ascending' : dir === 'desc' ? 'descending' : 'none') : undefined}
                  className={`sticky top-0 z-10 whitespace-nowrap border-b border-border bg-app-bg px-3 text-caption font-bold text-ink-secondary ${edge(index)} ${column.align === 'right' ? 'text-right' : ''} ${column.hideBelowSm ? 'hidden sm:table-cell' : ''}`}
                >
                  {column.sortValue ? (
                    <button
                      type="button"
                      onClick={() => toggle(column.key)}
                      className={`inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-control bg-transparent px-0 text-caption font-bold text-ink-secondary hover:text-ink ${focusRing} ${column.align === 'right' ? 'flex-row-reverse' : ''}`}
                    >
                      {column.label}
                      <SortArrow dir={dir} />
                    </button>
                  ) : (
                    <span className="inline-flex min-h-11 items-center">{column.label}</span>
                  )}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-surface">
          {sorted.map((row) => (
            <tr key={rowKey(row)} className="hover:bg-app-bg">
              {columns.map((column, index) => (
                <td
                  key={column.key}
                  className={`px-3 py-3 align-top ${edge(index)} ${column.align === 'right' ? 'text-right tabular-nums' : ''} ${column.hideBelowSm ? 'hidden sm:table-cell' : ''} ${column.className ?? ''}`}
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
