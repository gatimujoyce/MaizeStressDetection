import { useGrowthStage } from '../api/hooks'
import { useFarm } from '../farm/FarmContext'
import { focusRing } from './ui/styles'

// Where the maize is in its life, worked out from the planting date. Sits in the page header as the subtitle;
// "What does this mean?" opens the tip. Timings are approximate.
export default function GrowthStageCard() {
  const { selectedFarmId } = useFarm()
  const { data: stage } = useGrowthStage(selectedFarmId)
  if (!stage) return null

  if (!stage.known) {
    return (
      <p className="m-0 text-small text-ink-secondary">
        Growth stage: add a planting date to this plot to see it and to get alerts that fit your crop.
      </p>
    )
  }

  return (
    <details className="text-small text-ink-secondary">
      <summary className={`inline-flex min-h-11 cursor-pointer list-none flex-wrap items-center gap-x-2 rounded-control [&::-webkit-details-marker]:hidden ${focusRing}`}>
        <span className="font-bold text-ink">{stage.label}</span>
        {stage.days >= 0 && <span>· day {stage.days} after planting</span>}
        <span className="text-brand underline underline-offset-4">What does this mean?</span>
      </summary>
      <div className="flex max-w-prose flex-col gap-2 pb-2">
        <p className="m-0 text-body text-ink">{stage.tip}</p>
        <p className="m-0">Worked out from your planting date, so it can be a few days out. Our alerts take this stage into account.</p>
      </div>
    </details>
  )
}
