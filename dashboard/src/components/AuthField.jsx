import { EyeIcon, EyeOffIcon } from './Icons'

// One labelled input for the sign-in screens. A password field gets a show/hide button.
export default function AuthField({ id, label, type = 'text', placeholder, value, error, onChange, visible, onToggleVisibility, prefix, inputMode, maxLength, autoComplete, hint }) {
  const isPassword = type === 'password'

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-small font-normal text-[var(--color-text-primary)]">
        {label}
      </label>
      <div className={isPassword || prefix ? 'relative' : undefined}>
        <input
          id={id}
          type={isPassword && visible ? 'text' : type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          inputMode={inputMode}
          maxLength={maxLength}
          autoComplete={autoComplete}
          className={`min-h-12 border-[1.5px] px-3 py-2 ${isPassword ? 'pr-16' : ''} ${prefix ? 'pl-16' : ''} rounded-control text-body w-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus ${error
            ? 'border-[var(--color-critical-text)]'
            : 'border-control'
            }`}
        />
        {prefix && (
          <span className="absolute inset-y-0 left-3 flex items-center text-body text-[var(--color-text-secondary)]" aria-hidden="true">
            {prefix}
          </span>
        )}
        {isPassword && (
          <button
            type="button"
            onClick={onToggleVisibility}
            aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
            aria-pressed={visible}
            className="absolute inset-y-0 right-3 min-h-12 min-w-12 text-small font-normal text-[var(--color-brand)]"
          >
            {visible ? <EyeOffIcon /> : <EyeIcon />}
          </button>
        )}
      </div>
      {hint && !error && <p className="m-0 text-small text-[var(--color-text-secondary)]">{hint}</p>}
      {error && (
        <p className="text-small text-[var(--color-critical-text)]">{error}</p>
      )}
    </div>
  )
}
