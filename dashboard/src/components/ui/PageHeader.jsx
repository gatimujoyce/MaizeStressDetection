import { Link } from 'react-router-dom'
import { linkClass } from './styles'

// Page title row: the same on every screen. `subtitle` is one line of context (plot, growth stage);
// `aside` holds the one control that belongs with the title (e.g. the plot switcher);
// `back` is an optional { to, label } link shown above the title.
export default function PageHeader({ title, subtitle, aside, back }) {
  return (
    <header className="flex flex-col gap-3">
      {back && (
        <Link to={back.to} className={`inline-flex min-h-11 items-center self-start text-small ${linkClass}`}>
          <span aria-hidden="true" className="mr-1">←</span>
          {back.label}
        </Link>
      )}
      <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <h1 className="m-0 break-words text-page text-ink">{title}</h1>
          {subtitle && <div className="m-0 mt-1 text-body text-ink-secondary">{subtitle}</div>}
        </div>
        {aside && <div className="shrink-0 whitespace-nowrap">{aside}</div>}
      </div>
    </header>
  )
}
