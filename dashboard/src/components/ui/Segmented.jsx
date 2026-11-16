import { useRef } from 'react'
import { focusRing } from './styles'

// A small set of mutually exclusive choices (a time range, a tab of a list). Works as a radio group:
// Tab moves into it, the arrow keys move between options, the selected option is the one in the tab order.
// options: [{ key, label }]
export default function Segmented({ label, options, value, onChange, block = false }) {
  const refs = useRef([])
  const index = Math.max(0, options.findIndex((option) => option.key === value))

  const onKeyDown = (event) => {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[event.key]
    if (!step) return
    event.preventDefault()
    const next = (index + step + options.length) % options.length
    onChange(options[next].key)
    refs.current[next]?.focus()
  }

  return (
    <div
      role="radiogroup"
      aria-label={label}
      onKeyDown={onKeyDown}
      className={`${block ? 'flex w-full' : 'inline-flex'} gap-1 rounded-control border-[1.5px] border-control bg-surface p-1`}
    >
      {options.map((option, i) => {
        const selected = i === index
        return (
          <button
            key={option.key}
            ref={(el) => { refs.current[i] = el }}
            type="button"
            role="radio"
            aria-checked={selected}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(option.key)}
            className={`min-h-11 min-w-0 flex-1 cursor-pointer rounded-control px-2 py-1 text-center text-small font-bold leading-tight transition-colors duration-fast ease-out ${focusRing} ${
              selected ? 'bg-brand text-white' : 'bg-transparent text-ink hover:bg-app-bg'
            }`}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
