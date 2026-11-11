import { useLatestNpk } from '../api/hooks'

const NAMES = { nitrogen: 'Nitrogen', phosphorus: 'Phosphorus', potassium: 'Potassium' }
const SHORT = { nitrogen: 'N', phosphorus: 'P', potassium: 'K' }

function ago(value) {
  const minutes = Math.max(0, Math.round((Date.now() - Date.parse(value)) / 60000))
  if (minutes < 2) return 'just now'
  if (minutes < 90) return `${minutes} minutes ago`
  const hours = Math.round(minutes / 60)
  return hours < 48 ? `${hours} hours ago` : `${Math.round(hours / 24)} days ago`
}

// Soil nutrients from the plot's NPK sensor: the newest value of each, and whether it is under the warning level.
// The warning levels are provisional, so the wording stays an early warning, not a lab result.
export default function NpkTiles({ farm }) {
  const hasNpk = Boolean(farm?.has_npk_sensor ?? farm?.hasNpkSensor)
  const { data } = useLatestNpk(farm?.id ?? farm?.farm_id, hasNpk)
  if (!hasNpk || !data) return null
  const byName = Object.fromEntries((data.items ?? []).map((item) => [item.name, item]))
  return (
    <section aria-labelledby="npk-title" className="flex flex-col gap-3">
      <div>
        <h2 id="npk-title" className="m-0 text-title text-ink">Soil nutrients</h2>
        <p className="m-0 mt-1 text-small text-ink-secondary">
          From the NPK sensor, in mg/kg. This is an early warning, not a lab test.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {Object.keys(NAMES).map((name) => {
          const item = byName[name]
          return (
            <div key={name} className="rounded-card border border-control bg-surface p-4">
              <h3 className="m-0 text-small font-bold text-ink-secondary">{NAMES[name]} ({SHORT[name]})</h3>
              {item ? (
                <>
                  <p className="mb-0 mt-2 text-title text-ink">{item.value} <span className="text-small text-ink-secondary">mg/kg</span></p>
                  <p className={`mb-0 mt-1 text-small font-bold ${item.status === 'low' ? 'text-ink' : 'text-ink-secondary'}`}>
                    {item.status === 'low' ? `Low: under ${item.low} mg/kg` : `OK: above ${item.low} mg/kg`}
                  </p>
                  <p className="mb-0 mt-1 text-caption text-ink-secondary">Last value {ago(item.recorded_at)}</p>
                </>
              ) : (
                <p className="mb-0 mt-2 text-body text-ink">Not reporting</p>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}
