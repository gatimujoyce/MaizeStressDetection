// Placeholder block shaped like the content it stands in for. Pulses only when motion is allowed.
export default function Skeleton({ className = '', label }) {
  return (
    <div
      aria-hidden={label ? undefined : 'true'}
      aria-label={label}
      aria-busy={label ? 'true' : undefined}
      role={label ? 'status' : undefined}
      className={`rounded-card bg-neutral-bg motion-safe:animate-pulse ${className}`}
    />
  )
}
