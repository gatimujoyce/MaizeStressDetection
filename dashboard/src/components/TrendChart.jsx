import React, { useState } from 'react'

export default function TrendChart({ history = [] }) {
  const [showFull, setShowFull] = useState(false)
  const displayedHistory = showFull ? history : history.slice(-2)

  const getSeverityBadge = (sev) => {
    if (sev === 'healthy') return { label: 'Healthy', icon: '✓', classes: 'text-[var(--color-healthy-text)]' }
    if (sev === 'warning') return { label: 'Stress', icon: '⚠️', classes: 'text-[var(--color-warning-text)]' }
    return { label: 'Critical', icon: '✕', classes: 'text-[var(--color-critical-text)]' }
  }

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-sm p-5">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-base font-semibold m-0">Recent Field Trends</h3>
        <button
          onClick={() => setShowFull(!showFull)}
          className="text-[var(--color-brand)] text-sm bg-transparent border-none p-0 cursor-pointer min-h-0 min-w-0 font-medium underline"
        >
          {showFull ? 'Show Recent Only' : 'See Full History'}
        </button>
      </div>

      <div className="flex flex-col gap-3">
        {displayedHistory.length === 0 && (
          <p className="text-[var(--color-text-secondary)] text-sm">No history available yet.</p>
        )}
        {displayedHistory.map((item, idx) => {
          const badge = getSeverityBadge(item.severity)
          return (
            <div
              key={idx}
              className="flex justify-between items-center px-3 py-3 bg-[var(--color-bg)] rounded-sm"
            >
              <div>
                <strong className="block text-sm text-[var(--color-text-primary)]">{item.date}</strong>
                <span className="text-xs text-[var(--color-text-secondary)]">Stage: {item.stage}</span>
              </div>
              <div className={`flex items-center gap-1.5 font-medium text-sm ${badge.classes}`}>
                <span>{badge.icon}</span>
                <span>{badge.label}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}