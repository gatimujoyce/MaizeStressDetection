import React from 'react'
import { CheckIcon, WarningIcon, ErrorIcon, InfoIcon } from './Icons'

export default function StatCard({ label, value, status = 'neutral', subtext }) {
  const statusStyles = {
    healthy: { bg: 'var(--color-healthy-bg)', text: 'var(--color-healthy-text)', Icon: CheckIcon },
    warning: { bg: 'var(--color-warning-bg)', text: 'var(--color-warning-text)', Icon: WarningIcon },
    critical: { bg: 'var(--color-critical-bg)', text: 'var(--color-critical-text)', Icon: ErrorIcon },
    neutral: { bg: 'var(--color-neutral-bg)', text: 'var(--color-neutral-text)', Icon: InfoIcon }
  }

  const active = statusStyles[status] || statusStyles.neutral
  const IconComponent = active.Icon

  return (
    <div style={{
      backgroundColor: active.bg,
      color: active.text,
      border: '1px solid var(--color-border)',
      borderRadius: '2px',
      padding: '1rem 1.25rem',
      flex: '1 1 200px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        <IconComponent color={active.text} size={14} />
        <span>{label}</span>
      </div>
      <div style={{ fontSize: '1.4rem', fontWeight: '700', marginTop: '0.4rem', color: active.text }}>
        {value}
      </div>
      {subtext && (
        <div style={{ fontSize: '0.85rem', marginTop: '0.25rem', opacity: 0.9 }}>
          {subtext}
        </div>
      )}
    </div>
  )
}