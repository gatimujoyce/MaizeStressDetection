import { Link, Navigate } from 'react-router-dom'
import { useAlerts, useFarmHistory, useFarmStatus, useLatestReadingClassification, useLatestReadings } from '../../api/hooks'
import AlertCard from '../../components/AlertCard'
import AttentionAlert from '../../components/AttentionAlert'
import EmptyPlotState from '../../components/EmptyPlotState'
import GrowthStageCard from '../../components/GrowthStageCard'
import PlotSwitcher from '../../components/PlotSwitcher'
import ReadingTile from '../../components/ReadingTile'
import SensorSetupRow from '../../components/SensorSetupRow'
import TrendChart from '../../components/TrendChart'
import VerdictPanel from '../../components/VerdictPanel'
import Card, { SectionHeader } from '../../components/ui/Card'
import Notice from '../../components/ui/Notice'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { buttonClass, linkClass } from '../../components/ui/styles'
import useArrivals from '../../components/ui/useArrivals'
import useNow from '../../components/ui/useNow'
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

const STALE_AFTER_MS = 3 * 60 * 60 * 1000

function timeAgo(value, now) {
  const t = Date.parse(value)
  if (Number.isNaN(t)) return null
  const minutes = Math.max(0, Math.round((now - t) / 60000))
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`
  const days = Math.floor(hours / 24)
  return `${days} ${days === 1 ? 'day' : 'days'} ago`
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
          <span className="text-small font-normal text-ink-secondary">
            {getDaysSince(plantingDate)} days since planting
          </span>
        </span>
      ),
    },
    waterSource && { label: 'Water source', value: waterSource },
    seedVariety && { label: 'Seed variety', value: seedVariety },
    { label: 'Sensors', value: <SensorSetupRow farm={farm} />, wide: true },
  ].filter(Boolean)

  if (!rows.length) return null

  return (
    <Card aria-labelledby="plot-details-title">
      <SectionHeader id="plot-details-title" title="Plot details" />
      <dl className="m-0 grid grid-cols-1 gap-x-6 gap-y-3 text-left sm:grid-cols-2 lg:grid-cols-3">
        {rows.map(({ label, value, wide }) => (
          <div key={label} className={`min-w-0 ${wide ? 'sm:col-span-2 lg:col-span-3' : ''}`}>
            <dt className="text-small text-ink-secondary">{label}</dt>
            <dd className="m-0 break-words text-body font-bold text-ink">{value}</dd>
          </div>
        ))}
      </dl>
    </Card>
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
    isSuccess: alertsLoaded,
    isError: alertsError,
    isFetching: alertsFetching,
    refetch: retryAlerts,
  } = useAlerts(selectedFarmId)
  const { data: history = [] } = useFarmHistory(selectedFarmId)
  const { data: classification = null } = useLatestReadingClassification(selectedFarmId)
  const now = useNow()
  const ongoingSensorAlerts = alerts.filter((a) => a.source === 'sensor' && !a.resolved_at)
  const newestFirst = [...alerts].sort((a, b) => (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0))
  // Ongoing alerts are shown once, at the top; the recent list holds the rest.
  const recentAlerts = newestFirst.filter((a) => !ongoingSensorAlerts.includes(a)).slice(0, 3)
  const hiddenAlertCount = alerts.length - ongoingSensorAlerts.length - recentAlerts.length
  const arrived = useArrivals(alerts.map((a) => a.alert_id), alertsLoaded)
  const readingAge = readings?.recorded_at ? now - Date.parse(readings.recorded_at) : null
  const readingIsStale = readingAge !== null && readingAge > STALE_AFTER_MS
  const soilType = SOIL_PROFILES[selectedFarm?.soil_type] ? selectedFarm.soil_type : 'loam'
  const soilProfile = SOIL_PROFILES[soilType]
  const soilScale = moistureScale(soilType)
  const humidityZone = readings ? zoneFor(humidityScale(), readings.humidity) : null

  if (!farmsLoading && !hasFarms) return <Navigate to="/onboarding" replace />

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={selectedFarm?.farm_name || status?.farm_name || 'Your field'}
        aside={<PlotSwitcher />}
      />
      <GrowthStageCard />

      {readingIsStale && (
        <Notice tone="neutral">
          <p>The sensor has not reported for a while. These numbers may be out of date.</p>
        </Notice>
      )}

      {ongoingSensorAlerts.length > 0 && (
        <section aria-labelledby="attention-title" className="flex flex-col gap-3">
          <h2 id="attention-title" className="m-0 text-title text-ink">Needs attention now</h2>
          {ongoingSensorAlerts.map((alert) => (
            <AttentionAlert
              key={alert.alert_id}
              alert={alert}
              farmId={selectedFarmId}
              titleSuffix=" in your plot"
              showAllLink
              arrived={arrived(alert.alert_id)}
            />
          ))}
        </section>
      )}

      {status?.has_data === false ? (
        <EmptyPlotState plotName={selectedFarm?.farm_name || status?.farm_name || 'this plot'} />
      ) : (
        <VerdictPanel
          status={status}
          action={getFusedPredictionCopy(status?.fused_prediction).action}
        />
      )}

      {status?.has_data !== false && (
        <Link to="/check-in" className={`${buttonClass({ block: true })} sm:w-auto sm:self-start sm:px-8`}>
          Check my maize
        </Link>
      )}

      {readingsError ? (
        <Notice tone="critical" onRetry={() => retryReadings()} retrying={readingsFetching}>
          <p>Could not load field readings.</p>
        </Notice>
      ) : readings && (
        <section aria-labelledby="field-readings-title" className="motion-reveal flex flex-col gap-3">
          <div>
            <h2 id="field-readings-title" className="m-0 text-title text-ink">
              Field readings
            </h2>
            <p className="m-0 mt-1 text-small text-ink-secondary">
              {readings.recorded_at ? `Last reading ${timeAgo(readings.recorded_at, now)}.` : ''}
              {classification?.title ? ` The sensor model reads it as: ${classification.title}.` : ''}
            </p>
          </div>
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
            <Skeleton key={card} className="h-48" />
          ))}
        </section>
      )}
      {!readings && !readingsLoading && !readingsError && selectedFarmId && (
        <p className="m-0 text-small text-ink-secondary">
          No sensor readings recorded for this plot yet.
        </p>
      )}

      {status?.has_data !== false && !(alerts.length > 0 && recentAlerts.length === 0) && (
        <section className="flex flex-col gap-3" aria-labelledby="alerts-title">
          <SectionHeader
            id="alerts-title"
            title="Alerts"
            className="!mb-0"
            aside={hiddenAlertCount > 0 && (
              <Link to="/alerts" className={`inline-flex min-h-11 items-center text-small ${linkClass}`}>
                See all {alerts.length} alerts →
              </Link>
            )}
          />
          {alertsLoading ? (
            <Skeleton label="Loading alerts" className="h-28" />
          ) : alertsError ? (
            <Notice tone="critical" onRetry={() => retryAlerts()} retrying={alertsFetching}>
              <p>Could not load alerts.</p>
            </Notice>
          ) : alerts.length > 0 ? (
            <div className="flex flex-col gap-3">
              {recentAlerts.map((alert) => (
                <AlertCard key={alert.alert_id} alert={alert} farmId={selectedFarmId} arrived={arrived(alert.alert_id)} />
              ))}
            </div>
          ) : (
            <p className="m-0 text-body text-ink-secondary">
              No alerts right now. Your maize looks fine.
            </p>
          )}
        </section>
      )}

      <TrendChart history={history} />

      <PlotDetailsCard farm={selectedFarm} />
    </div>
  )
}