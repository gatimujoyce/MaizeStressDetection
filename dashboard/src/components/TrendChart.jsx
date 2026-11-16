import { useState } from 'react'
import Badge from './ui/Badge'
import Card, { SectionHeader } from './ui/Card'
import EmptyState from './ui/EmptyState'
import Notice from './ui/Notice'
import Skeleton from './ui/Skeleton'
import { buttonClass } from './ui/styles'

const SEVERITY_BADGES = {
  healthy: { tone: 'healthy', label: 'Healthy' },
  warning: { tone: 'warning', label: 'Stress' },
  critical: { tone: 'critical', label: 'Critical' },
  inconclusive: { tone: 'neutral', label: 'Inconclusive' },
}

const SHOWN_AT_FIRST = 5

// Past photo check-ins for the plot, newest first, as one list. Lives on the Trends screen (id "photo-checks",
// which the Home screen links to).
export default function TrendChart({ history = [], isLoading = false, isError = false, onRetry, retrying = false }) {
  const [showAll, setShowAll] = useState(false)
  const shown = showAll ? history : history.slice(0, SHOWN_AT_FIRST)

  return (
    <Card id="photo-checks" aria-labelledby="photo-checks-title" className="scroll-mt-6">
      <SectionHeader
        id="photo-checks-title"
        title="Photo check-ins"
        aside={history.length > SHOWN_AT_FIRST && (
          <button
            type="button"
            onClick={() => setShowAll((value) => !value)}
            aria-expanded={showAll}
            className={buttonClass({ variant: 'quiet', size: 'sm' })}
          >
            {showAll ? 'Show recent only' : `Show all ${history.length}`}
          </button>
        )}
      />
      {isLoading ? (
        <Skeleton label="Loading photo check-ins" className="h-32" />
      ) : isError ? (
        <Notice tone="critical" onRetry={onRetry} retrying={retrying}>
          <p>Could not load your photo check-ins.</p>
        </Notice>
      ) : shown.length === 0 ? (
        <EmptyState>
          <p>No photo check-ins yet. Each photo you check appears here with its result.</p>
        </EmptyState>
      ) : (
        <ul className="m-0 list-none divide-y divide-border p-0">
          {shown.map((item, idx) => {
            const badge = item.result
              ? { tone: item.result.tone || 'neutral', label: item.result.label }
              : SEVERITY_BADGES[item.severity]
            return (
              <li key={item.prediction_id ?? idx} className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 py-3 first:pt-0 last:pb-0">
                <div className="min-w-0">
                  <p className="m-0 text-body font-bold text-ink">{item.date}</p>
                  {item.stage && <p className="m-0 text-small text-ink-secondary">Stage: {item.stage}</p>}
                </div>
                {badge && <Badge tone={badge.tone}>{badge.label}</Badge>}
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}
