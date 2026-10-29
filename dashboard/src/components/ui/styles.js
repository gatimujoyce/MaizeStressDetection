// Shared class strings. Use these instead of re-typing button/card/field classes per view,
// so both the farmer and admin views stay on one spacing, type and shape scale.

const focusRing = 'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus'

const BUTTON_VARIANTS = {
  primary: 'bg-brand text-white hover:bg-brand-hover',
  secondary: 'border-2 border-brand bg-surface text-brand hover:bg-brand-tint',
  // Text-style action: keeps the 44px height but sits flush with surrounding text.
  quiet: 'bg-transparent !px-0 text-brand underline underline-offset-4',
}

const BUTTON_SIZES = {
  // Farmer screens: 48px targets, 17px label.
  md: 'min-h-12 px-5 text-body',
  // Admin and secondary inline actions: 44px targets.
  sm: 'min-h-11 px-4 text-small',
}

export function buttonClass({ variant = 'primary', size = 'md', block = false } = {}) {
  return [
    'inline-flex items-center justify-center gap-2 rounded-control font-bold no-underline',
    'transition-colors duration-fast ease-out disabled:cursor-not-allowed disabled:opacity-60',
    focusRing,
    BUTTON_VARIANTS[variant],
    BUTTON_SIZES[size],
    block ? 'w-full' : '',
  ].join(' ')
}

export const linkClass = `font-bold text-brand underline underline-offset-4 ${focusRing}`

export const fieldClass = `min-h-12 w-full rounded-control border-[1.5px] border-control bg-surface px-4 text-body text-ink ${focusRing}`

export const cardClass = 'rounded-card border border-border bg-surface p-4 sm:p-5'

// Tinted inner panel inside a card (e.g. "What to do", a reading cell).
export const insetClass = 'rounded-control bg-app-bg p-3'

export { focusRing }
