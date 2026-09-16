import React from 'react'

export default function FarmTable({ farms = [] }) {
  const getStatusBadge = (severity) => {
    if (severity === 'healthy') {
      return { bg: 'var(--color-healthy-bg)', text: 'var(--color-healthy-text)', icon: '✓', label: 'Healthy' }
    }
    if (severity === 'warning') {
      return { bg: 'var(--color-warning-bg)', text: 'var(--color-warning-text)', icon: '⚠️', label: 'Stress Detected' }
    }
    return { bg: 'var(--color-critical-bg)', text: 'var(--color-critical-text)', icon: '✕', label: 'Disease Found' }
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: 'var(--color-surface)', textAlign: 'left' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
            <th style={{ padding: '0.75rem 1rem' }}>Farm Name</th>
            <th style={{ padding: '0.75rem 1rem' }}>Fused Prediction</th>
            <th style={{ padding: '0.75rem 1rem' }}>Severity Status</th>
            <th style={{ padding: '0.75rem 1rem' }}>Last Check-in</th>
          </tr>
        </thead>
        <tbody>
          {farms.map((farm) => {
            const badge = getStatusBadge(farm.severity_level)
            return (
              <tr key={farm.farm_id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '0.75rem 1rem', fontWeight: '500' }}>{farm.name}</td>
                <td style={{ padding: '0.75rem 1rem' }}>{farm.fused_prediction}</td>
                <td style={{ padding: '0.75rem 1rem' }}>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    backgroundColor: badge.bg,
                    color: badge.text,
                    padding: '0.25rem 0.6rem',
                    borderRadius: '4px',
                    fontSize: '0.85rem',
                    fontWeight: '500'
                  }}>
                    <span>{badge.icon}</span>
                    <span>{badge.label}</span>
                  </span>
                </td>
                <td style={{ padding: '0.75rem 1rem', color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
                  {farm.last_checkin}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}