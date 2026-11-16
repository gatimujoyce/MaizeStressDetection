import { focusRing } from './styles'

const controlClass = `min-h-11 rounded-control border-[1.5px] border-control bg-surface px-3 text-small text-ink ${focusRing}`

// The search box: grows to fill the toolbar row.
export function SearchField({ label, value, onChange, placeholder }) {
  return (
    <label className="min-w-0 flex-1 basis-full sm:basis-64">
      <span className="sr-only">{label}</span>
      <input type="search" value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className={`w-full ${controlClass}`} />
    </label>
  )
}

export function FilterSelect({ id, label, value, onChange, options }) {
  return (
    <>
      <label className="sr-only" htmlFor={id}>{label}</label>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)} className={`max-w-full ${controlClass}`}>
        {options.map(([optionValue, optionLabel]) => <option key={optionValue} value={optionValue}>{optionLabel}</option>)}
      </select>
    </>
  )
}

// A yes/no filter in the toolbar ("Include archived farms").
export function FilterCheckbox({ label, checked, onChange }) {
  return (
    <label className={`flex min-h-11 cursor-pointer items-center gap-2 rounded-control border-[1.5px] border-control bg-surface px-3 text-small text-ink ${focusRing.replaceAll('focus-visible', 'focus-within')}`}>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="h-4 w-4 min-h-0 accent-brand" />
      {label}
    </label>
  )
}

// The one filter row of an admin table: search first, then filters, then the one action (pushed to the end).
export default function Toolbar({ children, action }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {children}
      {action && <div className="sm:ml-auto">{action}</div>}
    </div>
  )
}
