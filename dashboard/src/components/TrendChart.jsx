import React, { useState } from 'react'

export default function TrendChart({ history = [] }) {
  const [showFull, setShowFull] = useState(false)

  const displayedHistory = showFull ? history : history.slice(-2)

  const getSeverityBadge = (sev) => {
    if (sev === 'healthy') return { label: 'Healthy', icon: '✓', color: 'var(--color-healthy-text)' }
    if (sev === 'warning') return { label: 'Stress', icon: '⚠️', color: 'var(--color-warning-text)' }
    return { label: 'Critical', icon: '✕', color: 'var(--color-critical-text)' }
  }

  return (
    <div style={{
      backgroundColor: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: '8px',
      padding: '1.25rem'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Recent Field Trends</h3>
        <button
          onClick={() => setShowFull(!showFull)}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-brand)',
            cursor: 'pointer',
            padding: '0.25rem',
            fontSize: '0.9rem',
            minHeight: 'auto'
          }}
        >
          {showFull ? 'Show Recent Only' : 'See Full History'}
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {displayedHistory.map((item, idx) => {
          const badge = getSeverityBadge(item.severity)
          return (
            <div 
              key={idx} 
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.75rem',
                backgroundColor: 'var(--color-bg)',
                borderRadius: '6px'
              }}
            >
              <div>
                <strong style={{ display: 'block', fontSize: '0.95rem' }}>{item.date}</strong>
                <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                  Stage: {item.stage}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: badge.color, fontWeight: '500' }}>
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