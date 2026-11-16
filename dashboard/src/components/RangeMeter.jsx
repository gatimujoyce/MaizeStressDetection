const TONE_CLASSES = {
  healthy: 'bg-healthy-bg',
  warning: 'bg-warning-bg',
  neutral: 'bg-neutral-bg',
}

export default function RangeMeter({ value, scale, unit, valueText }) {
  const clampedValue = Math.max(scale.min, Math.min(scale.max, value))
  const position = Math.min(
    98,
    Math.max(2, ((clampedValue - scale.min) / (scale.max - scale.min)) * 100),
  )

  return (
    <div
      role="meter"
      aria-valuemin={scale.min}
      aria-valuemax={scale.max}
      aria-valuenow={value}
      aria-valuetext={valueText}
      className="relative mb-3 mt-2 h-6"
    >
      <div className="absolute inset-x-0 top-1/2 flex h-3.5 -translate-y-1/2 gap-0.5 overflow-hidden rounded-full border border-control">
        {scale.zones.map((zone, index) => {
          const width = ((zone.to - zone.from) / (scale.max - scale.min)) * 100
          return (
            <span
              key={`${zone.label}-${index}`}
              aria-hidden="true"
              className={`h-full min-w-0 ${TONE_CLASSES[zone.tone]} ${zone.tone === 'healthy' ? '' : 'meter-hatch'}`}
              style={{ width: `${width}%` }}
            />
          )
        })}
      </div>
      <span
        aria-hidden="true"
        className="absolute top-0 h-6 w-1 -translate-x-1/2 rounded-full bg-ink ring-2 ring-surface"
        style={{ left: `${position}%` }}
      />
      <span className="sr-only">{unit}</span>
    </div>
  )
}
