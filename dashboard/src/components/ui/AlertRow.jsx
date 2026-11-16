// The container for alert rows: one bordered list with a line between alerts, instead of a box per alert.
export function AlertList({ className = '', children, ...props }) {
  return (
    <ul className={`m-0 list-none divide-y divide-border overflow-hidden rounded-card border border-border p-0 ${className}`} {...props}>
      {children}
    </ul>
  )
}

// One alert in a list. The stripe colour, the icon and the words in the row all carry the severity, never colour alone.
//   tone     'critical' or 'warning' (anything else shows a neutral stripe)
//   tinted   true for an alert that needs attention now; earlier alerts sit on the plain surface
//   as       'li' inside a list, 'article' on its own
export default function AlertRow({ tone, tinted = false, as: Tag = 'li', className = '', children, ...props }) {
  const stripe = tone === 'critical' ? 'bg-critical-text' : tone === 'warning' ? 'bg-warning-text' : 'bg-control'
  const surface = tinted ? (tone === 'critical' ? 'bg-critical-bg' : 'bg-warning-bg') : 'bg-surface'
  return (
    <Tag className={`relative overflow-hidden py-4 pl-6 pr-4 ${surface} ${className}`} {...props}>
      <span aria-hidden="true" className={`absolute inset-y-0 left-0 w-1.5 ${stripe}`} />
      {children}
    </Tag>
  )
}
