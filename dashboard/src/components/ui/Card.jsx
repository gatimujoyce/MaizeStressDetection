import { cardClass } from './styles'

// The one container. Never put a Card inside a Card: group facts inside it with `divided` (a line between each
// direct child) or a DescriptionList instead.
//   flush    no padding, for a table or list that runs edge to edge
//   divided  each direct child becomes a group separated by a line
//   tone     'healthy' | 'warning' | 'critical' | 'neutral': a status panel. Only for the one status a page is about.
const TONES = {
  healthy: '!border-transparent !bg-healthy-bg text-healthy-text',
  warning: '!border-transparent !bg-warning-bg text-warning-text',
  critical: '!border-transparent !bg-critical-bg text-critical-text',
  neutral: '!border-transparent !bg-neutral-bg text-neutral-text',
}

export default function Card({ as: Tag = 'section', flush = false, divided = false, tone, className = '', children, ...props }) {
  const padding = flush ? 'overflow-hidden !p-0' : ''
  const groups = divided ? 'flex flex-col divide-y divide-border [&>*]:py-4 [&>*:first-child]:pt-0 [&>*:last-child]:pb-0 sm:[&>*]:py-6' : ''
  return (
    <Tag className={`${cardClass} ${padding} ${groups} ${TONES[tone] ?? ''} ${className}`} {...props}>
      {children}
    </Tag>
  )
}

// Heading row for a page section or a group inside a Card, with an optional item on the right (count, link, filter).
// h2 is a section title; h3 is a title inside a section and uses body size in bold.
export function SectionHeader({ id, title, description, as: Heading = 'h2', aside, className = '' }) {
  return (
    <div className={`mb-4 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 ${className}`}>
      <div className="min-w-0">
        <Heading id={id} className={`m-0 ${Heading === 'h2' ? 'text-section' : 'text-body font-bold'} text-ink`}>
          {title}
        </Heading>
        {description && <p className="m-0 mt-1 text-small text-ink-secondary">{description}</p>}
      </div>
      {aside}
    </div>
  )
}
