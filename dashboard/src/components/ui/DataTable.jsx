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

// Dense admin table: header stays visible while the body scrolls, sortable columns announce
// their state with aria-sort, numbers right-align in tabular figures.
// columns: [{ key, label, render(row), sortValue?(row), align?: 'right', className? }]
export default function DataTable({ caption, columns, rows, rowKey, initialSort, empty, maxHeight = 'max-h-[70vh]' }) {
  const [sort, setSort] = useState(initialSort ?? null)
  const sortColumn = columns.find((column) => column.key === sort?.key)
  const sorted = sortColumn?.sortValue
    ? [...rows].sort((a, b) => compare(sortColumn.sortValue(a), sortColumn.sortValue(b)) * (sort.dir === 'desc' ? -1 : 1))
    : rows

  const toggle = (key) =>
    setSort((current) => (current?.key === key ? { key, dir: current.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }))

  if (rows.length === 0) {
    return <p className="m-0 rounded-control bg-app-bg p-5 text-center text-small text-ink-secondary">{empty}</p>
  }

  return (
    <div className={`overflow-auto rounded-control border border-border ${maxHeight}`}>
      <table className="w-full min-w-[720px] border-collapse text-left text-small">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            {columns.map((column) => {
              const dir = sort?.key === column.key ? sort.dir : null
              return (
                <th
                  key={column.key}
                  scope="col"
                  aria-sort={column.sortValue ? (dir === 'asc' ? 'ascending' : dir === 'desc' ? 'descending' : 'none') : undefined}
                  className={`sticky top-0 z-10 border-b border-border bg-app-bg px-4 text-caption font-bold text-ink-secondary ${column.align === 'right' ? 'text-right' : ''}`}
                >
                  {column.sortValue ? (
                    <button
                      type="button"
                      onClick={() => toggle(column.key)}
                      className={`inline-flex min-h-11 items-center gap-1.5 rounded-control bg-transparent px-0 text-caption font-bold text-ink-secondary hover:text-ink ${focusRing} ${column.align === 'right' ? 'flex-row-reverse' : ''}`}
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
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={`px-4 py-3 align-top ${column.align === 'right' ? 'text-right tabular-nums' : ''} ${column.className ?? ''}`}
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
