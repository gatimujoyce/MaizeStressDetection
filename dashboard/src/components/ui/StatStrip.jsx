import Card from './Card'
import Skeleton from './Skeleton'

// A row of headline numbers in one card, split by lines, instead of a card per number.
// stats: [{ label, value, detail?, isLoading?, isError? }]. Each figure can come from a different request.
export default function StatStrip({ label, stats }) {
  return (
    <Card as="section" aria-label={label} className="!p-0">
      <dl className="m-0 grid grid-cols-1 divide-y divide-border sm:auto-cols-fr sm:grid-flow-col sm:divide-x sm:divide-y-0">
        {stats.map((stat) => (
          <div key={stat.label} className="flex flex-col gap-1 p-4 sm:p-6">
            <dt className="text-small text-ink-secondary">{stat.label}</dt>
            <dd className="m-0 text-figure tabular-nums text-ink">
              {stat.isLoading ? (
                <Skeleton label={`Loading ${stat.label.toLowerCase()}`} className="h-8 w-16" />
              ) : stat.isError ? (
                <span className="text-body font-bold text-ink-secondary">Unavailable</span>
              ) : (
                stat.value
              )}
            </dd>
            {stat.detail && !stat.isLoading && !stat.isError && <dd className="m-0 text-small text-ink-secondary">{stat.detail}</dd>}
          </div>
        ))}
      </dl>
    </Card>
  )
}
