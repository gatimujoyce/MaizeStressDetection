import { focusRing } from './styles'

const controlClass = `min-h-11 rounded-control border-[1.5px] border-control bg-surface px-3 text-small text-ink ${focusRing}`

// The same search + filter row on every admin panel.
export function SearchField({ label, value, onChange, placeholder }) {
  return (
    <label className="min-w-0 flex-1">
      <span className="sr-only">{label}</span>
      <input type="search" value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className={`w-full ${controlClass}`} />
    </label>
  )
}

export function FilterSelect({ id, label, value, onChange, options }) {
  return (
    <>
      <label className="sr-only" htmlFor={id}>{label}</label>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)} className={`font-bold ${controlClass}`}>
        {options.map(([optionValue, optionLabel]) => <option key={optionValue} value={optionValue}>{optionLabel}</option>)}
      </select>
    </>
  )
}

export default function Toolbar({ children }) {
  return <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">{children}</div>
}
