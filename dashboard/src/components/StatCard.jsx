import React from 'react'
import { CheckIcon, WarningIcon, ErrorIcon, InfoIcon } from './Icons'

export default function StatCard({ label, value, status = 'neutral', subtext, icon }) {
  const statusStyles = {
    healthy: {
      containerClass: 'bg-[var(--color-healthy-bg)] text-[var(--color-healthy-text)]',
      Icon: CheckIcon,
    },
    warning: {
      containerClass: 'bg-[var(--color-warning-bg)] text-[var(--color-warning-text)]',
      Icon: WarningIcon,
    },
    critical: {
      containerClass: 'bg-[var(--color-critical-bg)] text-[var(--color-critical-text)]',
      Icon: ErrorIcon,
    },
    neutral: {
      containerClass: 'bg-[var(--color-neutral-bg)] text-[var(--color-neutral-text)]',
      Icon: InfoIcon,
    },
  }

  const active = statusStyles[status] || statusStyles.neutral
  const IconComponent = active.Icon

  return (
    <div className={`${active.containerClass} border border-[var(--color-border)] rounded-sm p-4 flex-1 min-w-[200px]`}>
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider opacity-80">
        {icon ? (
          <span>{icon}</span>
        ) : (
          <IconComponent size={14} />
        )}
        <span>{label}</span>
      </div>
      <div className="text-2xl font-bold mt-1.5">{value}</div>
      {subtext && (
        <div className="text-xs mt-1 opacity-80">{subtext}</div>
      )}
    </div>
  )
}