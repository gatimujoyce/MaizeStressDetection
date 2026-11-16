// Label and value pairs as rows with a line between them, instead of a box per fact.
// items: [{ label, value, action?, key? }]. On phones the label sits above the value; from 640px they share a row.
export default function DescriptionList({ items, className = '' }) {
  return (
    <dl className={`m-0 divide-y divide-border ${className}`}>
      {items.map(({ label, value, action, key }) => (
        <div key={key ?? label} className="flex flex-col gap-1 py-3 first:pt-0 last:pb-0 sm:grid sm:grid-cols-[minmax(0,12rem)_minmax(0,1fr)_auto] sm:items-baseline sm:gap-4">
          <dt className="text-small text-ink-secondary">{label}</dt>
          <dd className="m-0 min-w-0 break-words text-body text-ink">{value}</dd>
          {action ? <div className="sm:justify-self-end">{action}</div> : <span className="hidden sm:block" />}
        </div>
      ))}
    </dl>
  )
}
