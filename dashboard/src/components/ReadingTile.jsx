import RangeMeter from './RangeMeter'
import Badge from './ui/Badge'
import { cardClass } from './ui/styles'
import { zoneFor } from '../content/sensorModel'

export default function ReadingTile({ title, value, unit, scale, caption, note }) {
  const zone = zoneFor(scale, value)
  const formattedValue = Number(value).toLocaleString('en-GB', { maximumFractionDigits: 2 })
  const valueText = `${formattedValue}${unit ? ` ${unit}` : ''}, ${zone.label}`

  return (
    <article className={cardClass}>
      <h3 className="mb-2 mt-0 text-heading text-ink">{title}</h3>
      <div className="mb-1 flex flex-wrap items-center gap-3">
        <p className="m-0 text-stat tabular-nums text-ink">
          {formattedValue}
          {unit && <span className="ml-1 text-title">{unit}</span>}
        </p>
        <Badge tone={zone.tone}>{zone.label}</Badge>
      </div>
      <RangeMeter value={value} scale={scale} unit={unit} valueText={valueText} />
      <p className="m-0 text-small text-ink-secondary">{caption}</p>
      {note && <p className="mb-0 mt-2 text-small text-ink-secondary">{note}</p>}
    </article>
  )
}
