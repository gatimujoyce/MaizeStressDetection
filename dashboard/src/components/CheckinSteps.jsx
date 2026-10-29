import { CheckIcon } from './Icons'

const STEPS = ['Photo', 'Review', 'Result']

// Where the farmer is in the photo check: take a photo, look at it, get the result.
export default function CheckinSteps({ current }) {
  return (
    <ol aria-label="Check-in steps" className="m-0 grid list-none grid-cols-3 gap-2 p-0">
      {STEPS.map((label, index) => {
        const done = index < current
        const active = index === current
        return (
          <li key={label} aria-current={active ? 'step' : undefined} className="flex flex-col gap-2">
            <span
              aria-hidden="true"
              className={`h-1.5 rounded-full transition-colors duration-base ease-out ${done || active ? 'bg-brand' : 'bg-border'}`}
            />
            <span className={`flex items-center gap-1.5 text-small ${active ? 'font-bold text-ink' : 'text-ink-secondary'}`}>
              {done ? (
                <span className="flex text-brand"><CheckIcon size={14} /></span>
              ) : (
                <span aria-hidden="true" className="tabular-nums">{index + 1}.</span>
              )}
              {label}
              {done && <span className="sr-only">(done)</span>}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
