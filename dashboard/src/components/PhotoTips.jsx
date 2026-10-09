import { useState } from 'react'

const TIPS_COLLAPSED_KEY = 'msm_tips_collapsed'

const photoExamples = [
  { image: 'tips-good.webp', badge: 'Good', good: true, caption: 'One leaf, flat, in daylight' },
  { image: 'tips-far.webp', badge: 'Avoid', good: false, caption: 'Too many leaves in one photo' },
  { image: 'tips-blurry.webp', badge: 'Avoid', good: false, caption: 'Blurry. Tap the leaf on your screen to focus' },
  { image: 'tips-dark.webp', badge: 'Avoid', good: false, caption: 'Too dark. Move into daylight' },
]

function TipBadge({ good, children }) {
  return (
    <span className={`inline-flex min-h-8 items-center gap-1.5 rounded-full px-2.5 text-[15px] font-bold ${good ? 'bg-healthy-bg text-healthy-text' : 'bg-warning-bg text-warning-text'}`}>
      {good ? (
        <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="m4 10 4 4 8-8" />
        </svg>
      ) : (
        <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="m5 5 10 10M15 5 5 15" />
        </svg>
      )}
      {children}
    </span>
  )
}

function readCollapsedPreference() {
  try {
    return localStorage.getItem(TIPS_COLLAPSED_KEY) === 'true'
  } catch (error) {
    console.error('Unable to read photo tips preference', error)
    return false
  }
}

export default function PhotoTips() {
  const [isCollapsed, setIsCollapsed] = useState(readCollapsedPreference)

  const handleToggle = (event) => {
    const collapsed = !event.currentTarget.open
    setIsCollapsed(collapsed)
    try {
      localStorage.setItem(TIPS_COLLAPSED_KEY, String(collapsed))
    } catch (error) {
      console.error('Unable to save photo tips preference', error)
    }
  }

  return (
    <details
      open={!isCollapsed}
      onToggle={handleToggle}
      className="mb-5 rounded-2xl border border-border bg-surface p-4"
    >
      <summary className="flex min-h-12 cursor-pointer items-center rounded-xl text-[17px] font-bold text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand">
        How to take a clear photo
      </summary>
      <div role="group" aria-label="Photo examples" className="mt-4 grid grid-cols-2 gap-3">
        {photoExamples.map((example) => (
          <figure key={example.image} className="min-w-0">
            <div className="relative">
              <img
                src={`/images/${example.image}`}
                alt=""
                width="240"
                height="240"
                loading="lazy"
                decoding="async"
                className="aspect-square w-full rounded-xl object-cover"
              />
              <div className="absolute left-2 top-2">
                <TipBadge good={example.good}>{example.badge}</TipBadge>
              </div>
            </div>
            <figcaption className="mt-2 text-[15px] text-ink">
              {example.caption}
            </figcaption>
          </figure>
        ))}
      </div>
    </details>
  )
}
