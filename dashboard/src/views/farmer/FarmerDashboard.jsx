import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAlerts, useFarmHistory, useFarmStatus, useLatestReadingClassification, useLatestReadings } from '../../api/hooks'
import AlertCard from '../../components/AlertCard'
import EmptyPlotState from '../../components/EmptyPlotState'
import PlotSwitcher from '../../components/PlotSwitcher'
import ReadingTile from '../../components/ReadingTile'
import TrendChart from '../../components/TrendChart'
import VerdictPanel from '../../components/VerdictPanel'
import { getFusedPredictionCopy } from '../../content/farmerCopy'
import { humidityScale, moistureScale, SOIL_PROFILES, temperatureScale, zoneFor } from '../../content/sensorModel'
import { useFarm } from '../../farm/FarmContext'

function getDisplayValue(value) {
  if (value === null || value === undefined) return null
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : null
  const text = String(value).trim()
  return !text || /^(null|undefined)$/i.test(text) ? null : text
}

function formatSoilType(value) {
  const soilType = getDisplayValue(value)
  if (!soilType) return null
  const label = SOIL_PROFILES[soilType]?.label ?? soilType.replace(/[_-]+/g, ' ')
  return label.replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function parsePlantingDate(value) {
  const dateText = getDisplayValue(value)
  if (!dateText) return null
  const datePart = dateText.match(/^(\d{4})-(\d{2})-(\d{2})/)
  let date
  if (datePart) {
    const [, year, month, day] = datePart
    date = new Date(Number(year), Number(month) - 1, Number(day))
    if (
      date.getFullYear() !== Number(year)
      || date.getMonth() !== Number(month) - 1
      || date.getDate() !== Number(day)
    ) return null
  } else {
    date = new Date(dateText)
  }
  return Number.isNaN(date.getTime()) ? null : date
}

function getDaysSince(date) {
  const today = new Date()
  const todayStart = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate())
  const plantingDay = Date.UTC(date.getFullYear(), date.getMonth(), date.getDate())
  return Math.max(0, Math.floor((todayStart - plantingDay) / 86400000))
}

const STRESS_TITLES = {
  heat_stress: 'Heat stress',
  drought_stress: 'Drought stress',
  waterlogging_risk: 'Waterlogging risk',
}
const STALE_AFTER_MS = 3 * 60 * 60 * 1000

function timeAgo(value) {
  const t = Date.parse(value)
  if (Number.isNaN(t)) return null
  const minutes = Math.max(0, Math.round((Date.now() - t) / 60000))
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`
  const days = Math.floor(hours / 24)
  return `${days} ${days === 1 ? 'day' : 'days'} ago`
}

function alertAdvice(alert) {
  if (!alert.message) return ''
  return alert.message.includes(': ') ? alert.message.split(': ').slice(1).join(': ') : alert.message
}

function SensorAlertBanner({ alert }) {
  const critical = alert.severity === 'critical'
  return (
    <Link
      to="/alerts"
      role="alert"
      className="flex flex-col gap-1 rounded-2xl border border-border p-4 no-underline"
      style={{
        background: critical ? 'var(--color-critical-bg)' : 'var(--color-warning-bg)',
        color: critical ? 'var(--color-critical-text)' : 'var(--color-warning-text)',
      }}
    >
      <span className="text-[17px] font-bold">
        {STRESS_TITLES[alert.stress_class] || 'Field alert'} in your plot
      </span>
      <span className="text-[15px] text-ink">{alertAdvice(alert)}</span>
      <span className="text-sm font-semibold underline">See all alerts →</span>
    </Link>
  )
}

function PlotDetailsCard({ farm }) {
  if (!farm) return null

  const farmName = getDisplayValue(farm.farm_name)
  const county = getDisplayValue(farm.county)
  const soilType = formatSoilType(farm.soil_type)
  const size = getDisplayValue(farm.sizeAcres)
  const plantingDate = parsePlantingDate(farm.plantingDate)
  const waterSource = getDisplayValue(farm.waterSource)
  const seedVariety = getDisplayValue(farm.seedVariety)
  const rows = [
    farmName && { label: 'Plot name', value: farmName },
    county && { label: 'County', value: county },
    soilType && { label: 'Soil type', value: soilType },
    size && {
      label: 'Size',
      value: `${size} ${Number(size) === 1 ? 'acre' : 'acres'}`,
    },
    plantingDate && {
      label: 'Planting date',
      value: (
        <span className="flex flex-wrap items-baseline gap-x-2">
          <span>{new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }).format(plantingDate)}</span>
          <span className="text-sm font-normal text-ink-secondary">
            {getDaysSince(plantingDate)} days since planting
          </span>
        </span>
      ),
    },
    waterSource && { label: 'Water source', value: waterSource },
    seedVariety && { label: 'Seed variety', value: seedVariety },
  ].filter(Boolean)

  if (!rows.length) return null

  return (
    <section
      aria-labelledby="plot-details-title"
      className="rounded-2xl border border-border bg-surface p-4"
    >
      <h2 id="plot-details-title" className="mb-3 text-[17px] font-bold text-ink">
        Plot details
      </h2>
      <dl className="m-0 grid grid-cols-1 gap-x-6 gap-y-3 text-left sm:grid-cols-2 lg:grid-cols-3">
        {rows.map(({ label, value }) => (
          <div key={label} className="min-w-0">
            <dt className="text-sm text-ink-secondary">{label}</dt>
            <dd className="m-0 break-words text-base font-semibold text-ink">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

export default function FarmerDashboard() {
  const { selectedFarmId, selectedFarm, isLoading: farmsLoading, hasFarms } = useFarm()
  const { data: status = null } = useFarmStatus(selectedFarmId)
  const {
    data: readings,
    isLoading: readingsLoading,
    isError: readingsError,
    isFetching: readingsFetching,
    refetch: retryReadings,
  } = useLatestReadings(selectedFarmId)
  const {
    data: alerts = [],
    isLoading: alertsLoading,
    isError: alertsError,
    isFetching: alertsFetching,
    refetch: retryAlerts,
  } = useAlerts(selectedFarmId)
  const { data: history = [] } = useFarmHistory(selectedFarmId)
  const { data: classification = null } = useLatestReadingClassification(selectedFarmId)
  const ongoingSensorAlerts = alerts.filter((a) => a.source === 'sensor' && !a.resolved_at)
  const newestFirst = [...alerts].sort((a, b) => (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0))
  const shownAlerts = [...ongoingSensorAlerts, ...newestFirst.filter((a) => !ongoingSensorAlerts.includes(a))].slice(0, 3)
  const readingAge = readings?.recorded_at ? Date.now() - Date.parse(readings.recorded_at) : null
  const readingIsStale = readingAge !== null && readingAge > STALE_AFTER_MS
  const soilType = SOIL_PROFILES[selectedFarm?.soil_type] ? selectedFarm.soil_type : 'loam'
  const soilProfile = SOIL_PROFILES[soilType]
  const soilScale = moistureScale(soilType)
  const humidityZone = readings ? zoneFor(humidityScale(), readings.humidity) : null
  const [isOffline, setIsOffline] = useState(!navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOffline(false)
    const handleOffline = () => setIsOffline(true)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  if (!farmsLoading && !hasFarms) return <Navigate to="/onboarding" replace />

  return (
    <div className="flex flex-col gap-6">
      {isOffline && (
        <div
          role="status"
          className="rounded-xl bg-neutral-bg p-4 text-[15px] text-neutral-text"
        >
          You are offline. Showing the last data saved on your phone.
        </div>
      )}

      <header className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="m-0 text-[30px] font-bold text-ink">
          {selectedFarm?.farm_name || status?.farm_name || 'Your field'}
        </h1>
        <PlotSwitcher />
      </header>

      {ongoingSensorAlerts.map((alert) => (
        <SensorAlertBanner key={alert.alert_id} alert={alert} />
      ))}

      <PlotDetailsCard farm={selectedFarm} />

      {status?.has_data === false ? (
        <EmptyPlotState plotName={selectedFarm?.farm_name || status?.farm_name || 'this plot'} />
      ) : (
        <VerdictPanel
          status={status}
          action={getFusedPredictionCopy(status?.fused_prediction).action}
        />
      )}

      {status?.has_data !== false && (
        <Link
          to="/check-in"
          className="flex min-h-[52px] w-full items-center justify-center rounded-xl bg-brand px-5 py-3 text-center text-[17px] font-bold text-white hover:bg-brand-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand sm:w-auto sm:self-start sm:px-8"
        >
          Check my maize
        </Link>
      )}

      {readingsError ? (
        <div role="alert" className="text-[15px] text-critical-text">
          <p>Could not load field readings.</p>
          <button
            type="button"
            onClick={() => retryReadings()}
            disabled={readingsFetching}
            className="min-h-11 rounded-xl border border-brand px-4 py-2 font-semibold text-brand disabled:opacity-60"
          >
            {readingsFetching ? 'Retrying…' : 'Retry'}
          </button>
        </div>
      ) : readings && (
        <section aria-labelledby="field-readings-title" className="flex flex-col gap-3">
          <h2 id="field-readings-title" className="m-0 text-[21px] font-bold text-ink">
            Field readings
          </h2>
          <p className="m-0 text-[15px] text-ink-secondary">
            {readings.recorded_at ? `Last reading ${timeAgo(readings.recorded_at)}.` : ''}
            {classification?.title ? ` The sensor model reads it as: ${classification.title}.` : ''}
          </p>
          {readingIsStale && (
            <p role="status" className="m-0 rounded-xl bg-neutral-bg p-3 text-[15px] text-neutral-text">
              The sensor has not reported for a while. These numbers may be out of date.
            </p>
          )}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <ReadingTile
              title="Soil moisture"
              value={readings.soil_moisture}
              unit="%"
              scale={soilScale}
              caption={`Good for ${soilProfile.label}: ${soilScale.goodRange[0]}-${soilScale.goodRange[1]}%`}
            />
            <ReadingTile
              title="Temperature"
              value={readings.temperature}
              unit="°C"
              scale={temperatureScale()}
              caption="Comfortable: 18-29°C. Heat stress from 32°C."
            />
            <ReadingTile
              title="Air humidity"
              value={readings.humidity}
              unit="%"
              scale={humidityScale()}
              caption="Usual range: 30-80%."
              note={humidityZone?.label === 'Humid' ? 'Humid air helps leaf diseases spread.' : undefined}
            />
          </div>
        </section>
      )}
      {!readings && readingsLoading && status?.has_data === true && (
        <section aria-label="Loading field readings" aria-busy="true" className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {[1, 2, 3].map((card) => (
            <div key={card} className="h-40 animate-pulse rounded-2xl border border-border bg-neutral-bg" />
          ))}
        </section>
      )}
      {!readings && !readingsLoading && !readingsError && selectedFarmId && (
        <p className="text-[15px] text-ink-secondary">
          No sensor readings recorded for this plot yet.
        </p>
      )}

      {status?.has_data !== false && (
        <section className="flex flex-col gap-3" aria-labelledby="alerts-title">
          <h2 id="alerts-title" className="m-0 text-[21px] font-bold text-ink">
            Alerts
          </h2>
          {alertsLoading ? (
            <p className="text-[15px] text-ink-secondary">Loading alerts…</p>
          ) : alertsError ? (
            <div role="alert" className="text-[15px] text-critical-text">
              <p>Could not load alerts.</p>
              <button
                type="button"
                onClick={() => retryAlerts()}
                disabled={alertsFetching}
                className="min-h-11 rounded-xl border border-brand px-4 py-2 font-semibold text-brand disabled:opacity-60"
              >
                {alertsFetching ? 'Retrying…' : 'Retry'}
              </button>
            </div>
          ) : alerts.length > 0 ? (
            <div className="flex flex-col gap-3">
              {shownAlerts.map((alert) => (
                <AlertCard key={alert.alert_id} alert={alert} farmId={selectedFarmId} />
              ))}
              {alerts.length > shownAlerts.length && (
                <Link to="/alerts" className="text-[15px] font-semibold text-brand underline">
                  See all {alerts.length} alerts →
                </Link>
              )}
            </div>
          ) : (
            <p className="text-[17px] text-ink-secondary">
              No alerts right now. Your maize looks fine.
            </p>
          )}
        </section>
      )}

      <div className="[&_button]:min-h-12 [&_button]:text-[15px] [&_h3]:text-[17px] [&_p]:text-[15px] [&_span]:text-[15px] [&_strong]:text-[15px]">
        <TrendChart history={history} />
      </div>
    </div>
  )
}