import { getFusedPredictionCopy, getNutrientStatusLabel } from '../content/farmerCopy'
import Badge from './ui/Badge'
import Skeleton from './ui/Skeleton'
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
      <Skeleton label="Loading latest field status" className="min-h-[463px] sm:min-h-[308px]" />
    )
  }

  const severity = verdictStyles[status.severity_level] ? status.severity_level : 'neutral'
  const className = verdictStyles[severity]
  const copy = getFusedPredictionCopy(status.fused_prediction)
  const resolvedAction = action ?? copy.action

  return (
    <section
      aria-labelledby="verdict-title"
      className={`motion-reveal relative rounded-card p-5 sm:p-6 ${className}`}
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
            <h2 id="verdict-title" className="m-0 text-display">
              {copy.headline}
            </h2>
            <p className="m-0 text-body">{copy.support}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Badge tone={severity}>{copy.chipLabel}</Badge>
            {status.nutrient_status != null && (
              <Badge tone={getNutrientStatusLabel(status.nutrient_status) === 'Nutrients look fine' ? 'healthy' : 'neutral'}>
                {getNutrientStatusLabel(status.nutrient_status)}
              </Badge>
            )}
          </div>
          <div className="rounded-control bg-surface p-4 text-ink">
            <LeafRule className="text-brand" />
            <p className="mb-1 mt-2 text-heading">What to do</p>
            <p className="m-0 text-body">{resolvedAction}</p>
          </div>
        </div>
      </div>
    </section>
  )
}
