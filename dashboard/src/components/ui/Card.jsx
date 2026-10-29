import { cardClass } from './styles'

export default function Card({ as: Tag = 'section', className = '', children, ...props }) {
  return (
    <Tag className={`${cardClass} ${className}`} {...props}>
      {children}
    </Tag>
  )
}

// Heading row for a card or page section, with an optional item on the right (count, link, filter).
export function SectionHeader({ id, title, as: Heading = 'h2', aside, className = '' }) {
  return (
    <div className={`mb-3 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 ${className}`}>
      <Heading id={id} className={`m-0 ${Heading === 'h2' ? 'text-title' : 'text-heading'} text-ink`}>
        {title}
      </Heading>
      {aside}
    </div>
  )
}
