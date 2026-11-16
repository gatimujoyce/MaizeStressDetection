// What a section shows when it has nothing yet: one plain sentence saying why, and the next step if there is one.
export default function EmptyState({ title, children, action, className = '' }) {
  return (
    <div className={`flex flex-col items-start gap-2 ${className}`}>
      {title && <p className="m-0 text-body font-bold text-ink">{title}</p>}
      {children && <div className="text-body text-ink-secondary [&_p]:m-0">{children}</div>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
