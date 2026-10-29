import { useState } from 'react'
import { CheckIcon, ErrorIcon, InfoIcon, WarningIcon } from './Icons'
import Card, { SectionHeader } from './ui/Card'
import { buttonClass, insetClass } from './ui/styles'

export default function TrendChart({ history = [] }) {
  const [showFull, setShowFull] = useState(false)
  const displayedHistory = showFull ? history : history.slice(0, 2)

  const getSeverityBadge = (sev) => {
    if (sev === 'healthy') return { label: 'Healthy', Icon: CheckIcon, classes: 'text-healthy-text' }
    if (sev === 'warning') return { label: 'Stress', Icon: WarningIcon, classes: 'text-warning-text' }
    if (sev === 'critical') return { label: 'Critical', Icon: ErrorIcon, classes: 'text-critical-text' }
    if (sev === 'inconclusive') return { label: 'Inconclusive', Icon: InfoIcon, classes: 'text-ink-secondary' }
    return null
  }

  return (
    <Card aria-labelledby="trend-title">
      <SectionHeader
        id="trend-title"
        title="Recent Field Trends"
        as="h3"
        aside={history.length > 2 && (
          <button
            type="button"
            onClick={() => setShowFull(!showFull)}
            aria-expanded={showFull}
            className={buttonClass({ variant: 'quiet', size: 'sm' })}
          >
            {showFull ? 'Show Recent Only' : 'See Full History'}
          </button>
        )}
      />

      {displayedHistory.length === 0 ? (
        <p className="m-0 text-small text-ink-secondary">No history available yet.</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-2 p-0">
          {displayedHistory.map((item, idx) => {
            const badge = getSeverityBadge(item.severity)
            return (
              <li key={idx} className={`flex items-center justify-between gap-3 ${insetClass}`}>
                <div className="min-w-0">
                  <strong className="block text-small text-ink">{item.date}</strong>
                  {item.stage && (
                    <span className="text-small text-ink-secondary">Stage: {item.stage}</span>
                  )}
                </div>
                {badge && (
                  <span className={`flex shrink-0 items-center gap-1.5 text-small font-bold ${badge.classes}`}>
                    <badge.Icon size={16} />
                    <span>{badge.label}</span>
                  </span>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}
