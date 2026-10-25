import { useId } from 'react'

// Thin decorative rule made of small maize leaves. Colour comes from the
// parent text colour (for example className="text-brand").
export default function LeafRule({ className = '' }) {
  const id = useId().replace(/:/g, '')
  return (
    <svg width="100%" height="12" aria-hidden="true" focusable="false" className={className}>
      <defs>
        <pattern id={id} width="32" height="12" patternUnits="userSpaceOnUse">
          <path d="M0 6 H11 M21 6 H32" stroke="currentColor" strokeWidth="1.5" fill="none" opacity="0.55" />
          <path d="M11 6 C14 1 18 1 21 6 C18 11 14 11 11 6 Z" fill="currentColor" opacity="0.8" />
        </pattern>
      </defs>
      <rect width="100%" height="12" fill={`url(#${id})`} />
    </svg>
  )
}
