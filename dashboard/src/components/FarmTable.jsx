import React from 'react'

export default function FarmTable({ farms = [] }) {
  const getStatusBadge = (severity) => {
    if (severity === 'healthy') {
      return { classes: 'bg-[var(--color-healthy-bg)] text-[var(--color-healthy-text)]', icon: '✓', label: 'Healthy' }
    }
    if (severity === 'warning') {
      return { classes: 'bg-[var(--color-warning-bg)] text-[var(--color-warning-text)]', icon: '⚠️', label: 'Stress Detected' }
    }
    return { classes: 'bg-[var(--color-critical-bg)] text-[var(--color-critical-text)]', icon: '✕', label: 'Disease Found' }
  }

  if (farms.length === 0) {
    return (
      <p className="text-[var(--color-text-secondary)] text-sm">No farms registered yet.</p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-sm border border-[var(--color-border)]">
      <table className="w-full border-collapse bg-[var(--color-surface)] text-left text-sm">
        <thead>
          <tr className="border-b-2 border-[var(--color-border)] text-[var(--color-text-secondary)] text-xs uppercase tracking-wider">
            <th className="px-4 py-3">Farm Name</th>
            <th className="px-4 py-3">Fused Prediction</th>
            <th className="px-4 py-3">Severity Status</th>
            <th className="px-4 py-3">Last Check-in</th>
          </tr>
        </thead>
        <tbody>
          {farms.map((farm) => {
            const badge = getStatusBadge(farm.severity_level)
            return (
              <tr key={farm.farm_id} className="border-b border-[var(--color-border)] hover:bg-[var(--color-neutral-bg)] transition-colors">
                <td className="px-4 py-3 font-medium text-[var(--color-text-primary)]">{farm.name}</td>
                <td className="px-4 py-3 text-[var(--color-text-secondary)] capitalize">{farm.fused_prediction?.replace(/_/g, ' ')}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium ${badge.classes}`}>
                    <span>{badge.icon}</span>
                    <span>{badge.label}</span>
                  </span>
                </td>
                <td className="px-4 py-3 text-[var(--color-text-secondary)]">{farm.last_checkin}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}