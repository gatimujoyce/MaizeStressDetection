// Shared class strings. Use these instead of re-typing button/card/field classes per view,
// so both the farmer and admin views stay on one spacing, type and shape scale.

const focusRing = 'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus'

const BUTTON_VARIANTS = {
  primary: 'bg-brand text-white hover:bg-brand-hover',
  secondary: 'border-[1.5px] border-brand bg-surface text-brand hover:bg-brand-tint',
  // Text-style action: keeps the 44px height but sits flush with surrounding text.
  quiet: 'bg-transparent !px-0 text-brand underline underline-offset-4',
}

const BUTTON_SIZES = {
  // Farmer screens: 48px targets, 17px label.
  md: 'min-h-12 px-6 text-body',
  // Admin and secondary inline actions: 44px targets.
  sm: 'min-h-11 px-4 text-small',
}

export function buttonClass({ variant = 'primary', size = 'md', block = false } = {}) {
  return [
    'inline-flex cursor-pointer items-center justify-center gap-2 rounded-control font-bold no-underline',
    'transition-colors duration-fast ease-out disabled:cursor-not-allowed disabled:opacity-60',
    focusRing,
    BUTTON_VARIANTS[variant],
    BUTTON_SIZES[size],
    block ? 'w-full' : '',
  ].join(' ')
}

export const linkClass = `font-bold text-brand underline underline-offset-4 ${focusRing}`

// Text inputs, selects and textareas. Pair with labelClass on the <label>.
export const fieldClass = `min-h-12 w-full rounded-control border-[1.5px] border-control bg-surface px-4 text-body text-ink ${focusRing}`

export const textareaClass = `w-full rounded-control border-[1.5px] border-control bg-surface px-4 py-3 text-body text-ink ${focusRing}`

export const labelClass = 'mb-2 block text-body font-bold text-ink'

// Admin forms: the same field, at the denser admin size. Wrap it in a label with adminLabelClass.
export const adminFieldClass = `mt-2 block min-h-11 w-full rounded-control border-[1.5px] border-control bg-surface px-3 text-small text-ink ${focusRing}`
export const adminLabelClass = 'block text-small font-bold text-ink'

// The one container style. Padding follows the spacing scale: 16px on phones, 24px from 640px.
export const cardClass = 'rounded-card border border-border bg-surface p-4 sm:p-6'

export { focusRing }
