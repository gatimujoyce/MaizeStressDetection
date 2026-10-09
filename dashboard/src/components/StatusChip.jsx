import { CheckIcon, ErrorIcon, InfoIcon, WarningIcon } from './Icons'

const statusStyles = {
  healthy: {
    className: 'bg-healthy-bg text-healthy-text',
    Icon: CheckIcon,
  },
  warning: {
    className: 'bg-warning-bg text-warning-text',
    Icon: WarningIcon,
  },
  critical: {
    className: 'bg-critical-bg text-critical-text',
    Icon: ErrorIcon,
  },
  neutral: {
    className: 'bg-neutral-bg text-neutral-text',
    Icon: InfoIcon,
  },
}

export default function StatusChip({ status, label }) {
  const { className, Icon } = statusStyles[status] ?? statusStyles.neutral

  return (
    <span className={`inline-flex w-fit self-start min-h-8 items-center gap-2 rounded-full px-3 py-1 text-[15px] font-bold ${className}`}>
      <span aria-hidden="true" className="flex">
        <Icon size={16} />
      </span>
      <span>{label}</span>
    </span>
  )
}
