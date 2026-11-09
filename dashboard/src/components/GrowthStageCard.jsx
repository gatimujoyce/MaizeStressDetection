import { useGrowthStage } from '../api/hooks'
import { useFarm } from '../farm/FarmContext'

// One line under the plot name: where the maize is in its life, worked out from the planting date.
// Tap "What does this mean?" for the tip. Timings are approximate.
export default function GrowthStageCard() {
  const { selectedFarmId } = useFarm()
  const { data: stage } = useGrowthStage(selectedFarmId)
  if (!stage) return null

  if (!stage.known) {
    return (
      <p className="m-0 -mt-3 text-small text-ink-secondary">
        Growth stage: add a planting date to this plot to see it and to get alerts that fit your crop.
      </p>
    )
  }

  return (
    <details className="-mt-3 text-small text-ink-secondary">
      <summary className="min-h-11 cursor-pointer list-none py-2 [&::-webkit-details-marker]:hidden">
        <span className="font-bold text-ink">{stage.label}</span>
        {stage.days >= 0 && <span> · day {stage.days} after planting</span>}
        <span className="ml-2 text-[var(--color-brand)] underline">What does this mean?</span>
      </summary>
      <p className="m-0 pb-2 text-body text-ink">{stage.tip}</p>
      <p className="m-0 pb-2">Worked out from your planting date, so it can be a few days out. Our alerts take this stage into account.</p>
    </details>
  )
}
