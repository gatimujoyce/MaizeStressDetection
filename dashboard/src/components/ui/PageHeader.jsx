// Page title row. `aside` holds the one control that belongs with the title (e.g. the plot switcher).
export default function PageHeader({ title, subtitle, aside }) {
  return (
    <header className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <h1 className="m-0 break-words text-display text-ink">{title}</h1>
        {subtitle && <p className="m-0 mt-1 text-small text-ink-secondary">{subtitle}</p>}
      </div>
      {aside}
    </header>
  )
}
