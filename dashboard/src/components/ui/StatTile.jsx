import { cardClass } from './styles'

// One headline number from a real query.
export default function StatTile({ label, value, isLoading, isError, detail }) {
  return (
    <article className={cardClass}>
      <p className="m-0 text-small font-bold text-ink-secondary">{label}</p>
      <p className="mb-0 mt-2 text-stat tabular-nums text-ink">
        {isLoading ? (
          <span role="status" aria-label="Loading" className="inline-block h-8 w-16 rounded-control bg-neutral-bg motion-safe:animate-pulse" />
        ) : isError ? (
          <span className="text-title text-ink-secondary">Unavailable</span>
        ) : (
          value
        )}
      </p>
      {detail && !isLoading && !isError && <p className="mb-0 mt-1 text-caption text-ink-secondary">{detail}</p>}
    </article>
  )
}
