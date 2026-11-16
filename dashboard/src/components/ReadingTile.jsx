import RangeMeter from './RangeMeter'
import Badge from './ui/Badge'
import { zoneFor } from '../content/sensorModel'

// One sensor reading inside the Field readings card: the value, its zone in words, and where it sits on the scale.
// A sensor that sent no value shows "Not reporting" in the same place, so the row keeps its shape.
export default function ReadingTile({ title, value, unit, scale, caption, note }) {
  if (!Number.isFinite(value)) {
    return (
      <div className="flex flex-col gap-2">
        <h3 className="m-0 text-body font-bold text-ink">{title}</h3>
        <p className="m-0 text-body text-ink">Not reporting</p>
        <p className="m-0 text-small text-ink-secondary">This sensor sent no value in the latest reading.</p>
      </div>
    )
  }

  const zone = zoneFor(scale, value)
  const formattedValue = Number(value).toLocaleString('en-GB', { maximumFractionDigits: 2 })
  const valueText = `${formattedValue}${unit ? ` ${unit}` : ''}, ${zone.label}`
  return (
    <div className="flex flex-col">
      <h3 className="m-0 mb-2 text-body font-bold text-ink">{title}</h3>
      <div className="mb-1 flex flex-wrap items-center gap-x-3 gap-y-2">
        <p className="m-0 text-figure tabular-nums text-ink">
          {formattedValue}
          {unit && <span className="ml-1 text-body font-bold">{unit}</span>}
        </p>
        <Badge tone={zone.tone}>{zone.label}</Badge>
      </div>
      <RangeMeter value={value} scale={scale} unit={unit} valueText={valueText} />
      <p className="m-0 text-small text-ink-secondary">{caption}</p>
      {note && <p className="m-0 mt-2 text-small text-ink-secondary">{note}</p>}
    </div>
  )
}
