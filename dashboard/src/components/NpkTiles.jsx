import { useLatestNpk } from '../api/hooks'
import { timeAgo } from '../content/dates'
import { SectionHeader } from './ui/Card'
import Skeleton from './ui/Skeleton'
import { buttonClass } from './ui/styles'

const NAMES = { nitrogen: 'Nitrogen', phosphorus: 'Phosphorus', potassium: 'Potassium' }
const SHORT = { nitrogen: 'N', phosphorus: 'P', potassium: 'K' }

// Soil nutrients from the plot's NPK sensor, as a group inside the Field readings card: the newest value of each,
// and whether it is under the warning level. The warning levels are provisional, so the wording stays an early
// warning, not a lab result. Shows nothing for a plot without an NPK sensor.
export default function NpkTiles({ farm }) {
  const hasNpk = Boolean(farm?.has_npk_sensor ?? farm?.hasNpkSensor)
  const { data, isLoading, isError, isFetching, refetch } = useLatestNpk(farm?.id ?? farm?.farm_id, hasNpk)
  if (!hasNpk) return null

  const byName = Object.fromEntries((data?.items ?? []).map((item) => [item.name, item]))
  return (
    <section aria-labelledby="npk-title">
      <SectionHeader
        id="npk-title"
        as="h3"
        title="Soil nutrients"
        description="From the NPK sensor, in mg/kg. This is an early warning, not a lab test."
      />
      {isLoading ? (
        <Skeleton label="Loading soil nutrients" className="h-20" />
      ) : isError ? (
        <div className="flex flex-wrap items-center gap-3">
          <p role="alert" className="m-0 text-small text-critical-text">Could not load soil nutrients.</p>
          <button type="button" onClick={() => refetch()} disabled={isFetching} className={buttonClass({ variant: 'secondary', size: 'sm' })}>
            {isFetching ? 'Retrying…' : 'Retry'}
          </button>
        </div>
      ) : (
        <dl className="m-0 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {Object.keys(NAMES).map((name) => {
            const item = byName[name]
            return (
              <div key={name} className="flex flex-col gap-1">
                <dt className="text-small font-bold text-ink-secondary">{NAMES[name]} ({SHORT[name]})</dt>
                {item ? (
                  <dd className="m-0 flex flex-col gap-1">
                    <span className="text-section tabular-nums text-ink">
                      {item.value} <span className="text-small font-normal text-ink-secondary">mg/kg</span>
                    </span>
                    <span className={`text-small ${item.status === 'low' ? 'font-bold text-ink' : 'text-ink-secondary'}`}>
                      {item.status === 'low' ? `Low: under ${item.low} mg/kg` : `OK: above ${item.low} mg/kg`}
                    </span>
                    <span className="text-small text-ink-secondary">Last value {timeAgo(item.recorded_at)}</span>
                  </dd>
                ) : (
                  <dd className="m-0 text-body text-ink">Not reporting</dd>
                )}
              </div>
            )
          })}
        </dl>
      )}
    </section>
  )
}
