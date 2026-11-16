import { Link, Navigate } from 'react-router-dom'
import { useAlerts, useFarmStatus, useLatestReadingClassification, useLatestReadings } from '../../api/hooks'
import AlertCard from '../../components/AlertCard'
import AttentionAlert from '../../components/AttentionAlert'
import EmptyPlotState from '../../components/EmptyPlotState'
import FollowUpCard from '../../components/FollowUpCard'
import GrowthStageCard from '../../components/GrowthStageCard'
import PlotSwitcher from '../../components/PlotSwitcher'
import ReadingTile from '../../components/ReadingTile'
import NpkTiles from '../../components/NpkTiles'
import SensorSetupRow from '../../components/SensorSetupRow'
import VerdictPanel from '../../components/VerdictPanel'
import { AlertList } from '../../components/ui/AlertRow'
import Card, { SectionHeader } from '../../components/ui/Card'
import DescriptionList from '../../components/ui/DescriptionList'
import EmptyState from '../../components/ui/EmptyState'
import Notice from '../../components/ui/Notice'
import Page from '../../components/ui/Page'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { buttonClass, linkClass } from '../../components/ui/styles'
import useArrivals from '../../components/ui/useArrivals'
import useNow from '../../components/ui/useNow'
import { getFusedPredictionCopy } from '../../content/farmerCopy'
import { formatDay, timeAgo } from '../../content/dates'
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

function PlotDetails({ farm }) {
  if (!farm) return null

  const county = getDisplayValue(farm.county)
  const soilType = formatSoilType(farm.soil_type)
  const size = getDisplayValue(farm.sizeAcres)
  const plantingDate = parsePlantingDate(farm.plantingDate)
  const waterSource = getDisplayValue(farm.waterSource)
  const seedVariety = getDisplayValue(farm.seedVariety)
  const items = [
    county && { label: 'County', value: county },
    soilType && { label: 'Soil type', value: soilType },
    size && { label: 'Size', value: `${size} ${Number(size) === 1 ? 'acre' : 'acres'}` },
    plantingDate && {
      label: 'Planting date',
      value: (
        <>
          {formatDay(plantingDate)}
          <span className="block text-small text-ink-secondary">{getDaysSince(plantingDate)} days since planting</span>
        </>
      ),
    },
    waterSource && { label: 'Water source', value: waterSource },
    seedVariety && { label: 'Seed variety', value: seedVariety },
    { label: 'Sensors', value: <SensorSetupRow farm={farm} /> },
  ].filter(Boolean)

  return (
    <Card aria-labelledby="plot-details-title">
      <SectionHeader id="plot-details-title" title="Plot details" />
      <DescriptionList items={items} />
    </Card>
  )
}

function FieldReadings({ farm, farmId }) {
  const now = useNow()
  const { data: readings, isLoading, isError, isFetching, refetch } = useLatestReadings(farmId)
  const { data: classification = null } = useLatestReadingClassification(farmId)
  const soilType = SOIL_PROFILES[farm?.soil_type] ? farm.soil_type : 'loam'
  const soilProfile = SOIL_PROFILES[soilType]
  const soilScale = moistureScale(soilType)
  const humidityZone = readings && Number.isFinite(readings.humidity) ? zoneFor(humidityScale(), readings.humidity) : null
  const readingIsStale = readings?.recorded_at && now - Date.parse(readings.recorded_at) > STALE_AFTER_MS

  const description = readings
    ? [
      readings.recorded_at ? `Last reading ${timeAgo(readings.recorded_at, now)}.` : '',
      classification?.title ? `The sensor model reads it as: ${classification.title}.` : '',
    ].filter(Boolean).join(' ')
    : undefined

  return (
    <Card divided aria-labelledby="field-readings-title">
      <div>
        <SectionHeader id="field-readings-title" title="Field readings" description={description} className="!mb-0" />
        {readingIsStale && (
          <Notice tone="neutral" className="mt-4">
            <p>The sensor has not reported for a while. These numbers may be out of date.</p>
          </Notice>
        )}
      </div>
      {isError ? (
        <Notice tone="critical" onRetry={() => refetch()} retrying={isFetching}>
          <p>Could not load field readings.</p>
        </Notice>
      ) : readings ? (
        <div className="motion-reveal grid grid-cols-1 gap-6 sm:grid-cols-3">
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
      ) : isLoading ? (
        <div aria-busy="true" className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <Skeleton label="Loading field readings" className="h-36" />
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
        </div>
      ) : (
        <EmptyState>
          <p>No sensor readings recorded for this plot yet.</p>
        </EmptyState>
      )}
      <NpkTiles farm={farm} />
    </Card>
  )
}

export default function FarmerDashboard() {
  const { selectedFarmId, selectedFarm, isLoading: farmsLoading, hasFarms } = useFarm()
  const {
    data: status = null,
    isError: statusError,
    isFetching: statusFetching,
    refetch: retryStatus,
  } = useFarmStatus(selectedFarmId)
  const {
    data: alerts = [],
    isLoading: alertsLoading,
    isSuccess: alertsLoaded,
    isError: alertsError,
    isFetching: alertsFetching,
    refetch: retryAlerts,
  } = useAlerts(selectedFarmId)
  const ongoingSensorAlerts = alerts.filter((a) => a.source === 'sensor' && !a.resolved_at)
  const newestFirst = [...alerts].sort((a, b) => (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0))
  // Ongoing alerts are shown once, at the top; the recent list holds the rest.
  const recentAlerts = newestFirst.filter((a) => !ongoingSensorAlerts.includes(a)).slice(0, 3)
  const hiddenAlertCount = alerts.length - ongoingSensorAlerts.length - recentAlerts.length
  const arrived = useArrivals(alerts.map((a) => a.alert_id), alertsLoaded)
  const plotName = selectedFarm?.farm_name || status?.farm_name

  if (!farmsLoading && !hasFarms) return <Navigate to="/onboarding" replace />

  return (
    <Page>
      <PageHeader title={plotName || 'Your field'} subtitle={<GrowthStageCard />} aside={<PlotSwitcher />} />

      <FollowUpCard />

      {ongoingSensorAlerts.length > 0 && (
        <section aria-labelledby="attention-title">
          <SectionHeader id="attention-title" title="Needs attention now" />
          <AlertList>
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
          </AlertList>
        </section>
      )}

      {statusError ? (
        <Notice tone="critical" onRetry={() => retryStatus()} retrying={statusFetching}>
          <p>Could not load the latest status of this plot.</p>
        </Notice>
      ) : status?.has_data === false ? (
        <EmptyPlotState plotName={plotName || 'this plot'} />
      ) : (
        <VerdictPanel status={status} action={getFusedPredictionCopy(status?.fused_prediction).action}>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-6">
            <Link to="/check-in" className={`${buttonClass({ block: true })} sm:w-auto sm:px-8`}>
              Check my maize
            </Link>
            <Link to="/trends#photo-checks" className={`inline-flex min-h-11 items-center self-center text-small sm:self-auto ${linkClass}`}>
              Past photo checks
            </Link>
          </div>
        </VerdictPanel>
      )}

      <FieldReadings farm={selectedFarm} farmId={selectedFarmId} />

      {status?.has_data !== false && !(alerts.length > 0 && recentAlerts.length === 0) && (
        <section aria-labelledby="alerts-title">
          <SectionHeader
            id="alerts-title"
            title="Alerts"
            aside={hiddenAlertCount > 0 && (
              <Link to="/alerts" className={`inline-flex min-h-11 items-center text-small ${linkClass}`}>
                See all {alerts.length} alerts
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
            <AlertList>
              {recentAlerts.map((alert) => (
                <AlertCard key={alert.alert_id} alert={alert} farmId={selectedFarmId} arrived={arrived(alert.alert_id)} />
              ))}
            </AlertList>
          ) : (
            <p className="m-0 text-body text-ink-secondary">
              No alerts right now. Your maize looks fine.
            </p>
          )}
        </section>
      )}

      <PlotDetails farm={selectedFarm} />
    </Page>
  )
}
