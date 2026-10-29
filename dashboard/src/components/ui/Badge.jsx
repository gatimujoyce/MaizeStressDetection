import { CheckIcon, ErrorIcon, InfoIcon, WarningIcon } from '../Icons'

const TONES = {
  healthy: { className: 'bg-healthy-bg text-healthy-text', Icon: CheckIcon },
  warning: { className: 'bg-warning-bg text-warning-text', Icon: WarningIcon },
  critical: { className: 'bg-critical-bg text-critical-text', Icon: ErrorIcon },
  neutral: { className: 'bg-neutral-bg text-neutral-text', Icon: InfoIcon },
}

const SIZES = {
  md: 'min-h-8 gap-2 px-3 text-small',
  sm: 'min-h-6 gap-1.5 px-2.5 text-caption',
}

// The one status chip. Tone is always paired with an icon and a text label, never colour alone.
export default function Badge({ tone = 'neutral', size = 'md', icon = true, children }) {
  const { className, Icon } = TONES[tone] ?? TONES.neutral
  return (
    <span className={`inline-flex w-fit shrink-0 items-center self-start rounded-full py-1 font-bold ${SIZES[size]} ${className}`}>
      {icon && (
        <span aria-hidden="true" className="flex">
          <Icon size={size === 'sm' ? 14 : 16} />
        </span>
      )}
      <span>{children}</span>
    </span>
  )
}
