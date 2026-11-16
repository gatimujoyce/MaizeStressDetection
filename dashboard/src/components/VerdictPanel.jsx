import { getFusedPredictionCopy, getNutrientStatusLabel } from '../content/farmerCopy'
import { formatDay } from '../content/dates'
import Badge from './ui/Badge'
import Card from './ui/Card'
import Skeleton from './ui/Skeleton'

const TONES = ['healthy', 'warning', 'critical', 'neutral']

// The plot's current status: the one primary thing on the Home screen.
// Headline and badge first, then what to do, then the one action (passed in as `children`).
export default function VerdictPanel({ status, action, children }) {
  if (!status) {
    return <Skeleton label="Loading latest field status" className="h-64" />
  }

  const severity = TONES.includes(status.severity_level) ? status.severity_level : 'neutral'
  const copy = getFusedPredictionCopy(status.fused_prediction)
  const resolvedAction = action ?? copy.action
  const checked = formatDay(status.created_at)
  const nutrientLabel = status.nutrient_status != null ? getNutrientStatusLabel(status.nutrient_status) : null

  return (
    <Card tone={severity} divided aria-labelledby="verdict-title" className="motion-reveal">
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
          <div className="flex flex-wrap gap-2">
            <Badge tone={severity}>{copy.chipLabel}</Badge>
            {nutrientLabel && (
              <Badge tone={nutrientLabel === 'Nutrients look fine' ? 'healthy' : 'neutral'}>{nutrientLabel}</Badge>
            )}
          </div>
          {checked && <p className="m-0 text-small">Checked {checked}</p>}
        </div>
        <h2 id="verdict-title" className="m-0 text-section">{copy.headline}</h2>
        <p className="m-0 text-body text-ink">{copy.support}</p>
      </div>
      <div className="flex flex-col gap-4 text-ink">
        <div>
          <h3 className="m-0 text-body font-bold">What to do</h3>
          <p className="m-0 mt-1 text-body">{resolvedAction}</p>
        </div>
        {children}
      </div>
    </Card>
  )
}
