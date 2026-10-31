import { CheckIcon, ErrorIcon, InfoIcon, WarningIcon } from '../Icons'
import { buttonClass } from './styles'

const TONES = {
  neutral: { className: 'bg-neutral-bg text-neutral-text', Icon: InfoIcon, role: 'status' },
  positive: { className: 'bg-positive-bg text-positive-text', Icon: CheckIcon, role: 'status' },
  warning: { className: 'bg-warning-bg text-warning-text', Icon: WarningIcon, role: 'status' },
  critical: { className: 'bg-critical-bg text-critical-text', Icon: ErrorIcon, role: 'alert' },
}

// Inline message for offline, stale data, load errors and unclear results.
// `onRetry` adds a Retry button; `retrying` shows its pending label.
export default function Notice({ tone = 'neutral', role: roleOverride, title, children, onRetry, retrying = false, action, className = '' }) {
  const { className: toneClass, Icon, role: toneRole } = TONES[tone] ?? TONES.neutral
  const role = roleOverride ?? toneRole
  return (
    <div role={role} className={`motion-enter flex gap-3 rounded-card p-4 ${toneClass} ${className}`}>
      <span aria-hidden="true" className="mt-1 flex shrink-0">
        <Icon size={18} />
      </span>
      <div className="flex min-w-0 flex-1 flex-col items-start gap-1">
        {title && <p className="m-0 text-heading">{title}</p>}
        {children && <div className="text-small text-ink [&_p]:m-0">{children}</div>}
        {(onRetry || action) && (
          <div className="mt-2 flex flex-wrap gap-3">
            {onRetry && (
              <button type="button" onClick={onRetry} disabled={retrying} className={buttonClass({ variant: 'secondary', size: 'sm' })}>
                {retrying ? 'Retrying…' : 'Retry'}
              </button>
            )}
            {action}
          </div>
        )}
      </div>
    </div>
  )
}
