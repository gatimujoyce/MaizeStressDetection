import { getFusedPredictionCopy, getNutrientStatusLabel } from '../content/farmerCopy'
import StatusChip from './StatusChip'
import MaizePlant from './illustrations/MaizePlant'
import LeafRule from './illustrations/LeafRule'
import DateStamp from './DateStamp'
import { plantVariantFor } from '../content/plantVariants'

const verdictStyles = {
  healthy: 'bg-healthy-bg text-healthy-text',
  warning: 'bg-warning-bg text-warning-text',
  critical: 'bg-critical-bg text-critical-text',
  neutral: 'bg-neutral-bg text-neutral-text',
}

export default function VerdictPanel({ status, action }) {
  if (!status) {
    return (
      <div
        aria-label="Loading latest field status"
        className="min-h-[463px] animate-pulse rounded-[24px] bg-neutral-bg p-6 sm:min-h-[308px]"
      />
    )
  }

  const severity = verdictStyles[status.severity_level] ? status.severity_level : 'neutral'
  const className = verdictStyles[severity]
  const copy = getFusedPredictionCopy(status.fused_prediction)
  const resolvedAction = action ?? copy.action

  return (
    <section
      aria-labelledby="verdict-title"
      className={`relative rounded-[24px] p-6 ${className}`}
    >
      <div className="flex flex-col gap-3 md:grid md:grid-cols-[176px_minmax(0,1fr)] md:gap-6">
        <div className="flex items-start justify-between md:justify-center">
          <MaizePlant
            variant={plantVariantFor(status.fused_prediction, status.severity_level)}
            className="w-28 shrink-0 md:w-40"
          />
          <div className="md:absolute md:right-6 md:top-6">
            <DateStamp date={status.created_at} />
          </div>
        </div>
        <div className="flex min-w-0 flex-col gap-3 md:pt-16">
          <div className="flex flex-col gap-3">
            <h2 id="verdict-title" className="m-0 text-[28px] font-bold leading-tight">
              {copy.headline}
            </h2>
            <p className="text-[17px]">{copy.support}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <StatusChip status={severity} label={copy.chipLabel} />
            <StatusChip
              status={getNutrientStatusLabel(status.nutrient_status) === 'Nutrients look fine' ? 'healthy' : 'neutral'}
              label={getNutrientStatusLabel(status.nutrient_status)}
            />
          </div>
          <div className="rounded-2xl bg-surface p-4 text-ink">
            <LeafRule className="text-brand" />
            <p className="mb-3 mt-2 font-bold">What to do</p>
            <p className="text-[17px]">{resolvedAction}</p>
          </div>
        </div>
      </div>
    </section>
  )
}
