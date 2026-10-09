import RangeMeter from './RangeMeter'
import StatusChip from './StatusChip'
import { zoneFor } from '../content/sensorModel'

export default function ReadingTile({ title, value, unit, scale, caption, note }) {
  const zone = zoneFor(scale, value)
  const formattedValue = Number(value).toLocaleString('en-GB', { maximumFractionDigits: 2 })
  const valueText = `${formattedValue}${unit ? ` ${unit}` : ''}, ${zone.label}`

  return (
    <article className="rounded-2xl border border-border bg-surface p-4">
      <h3 className="mb-2 text-[17px] font-bold text-ink">{title}</h3>
      <div className="mb-1 flex flex-wrap items-center gap-3">
        <p className="m-0 text-[32px] font-bold tabular-nums text-ink">
          {formattedValue}
          {unit && <span className="ml-1 text-[20px]">{unit}</span>}
        </p>
        <StatusChip status={zone.tone} label={zone.label} />
      </div>
      <RangeMeter value={value} scale={scale} unit={unit} valueText={valueText} />
      <p className="m-0 text-[15px] text-ink-secondary">{caption}</p>
      {note && <p className="mb-0 mt-2 text-[15px] text-ink-secondary">{note}</p>}
    </article>
  )
}
