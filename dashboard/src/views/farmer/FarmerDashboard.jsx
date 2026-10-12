import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAlerts, useFarmHistory, useFarmStatus, useLatestReadings } from '../../api/hooks'
import AlertCard from '../../components/AlertCard'
import EmptyPlotState from '../../components/EmptyPlotState'
import PlotSwitcher from '../../components/PlotSwitcher'
import ReadingTile from '../../components/ReadingTile'
import TrendChart from '../../components/TrendChart'
import VerdictPanel from '../../components/VerdictPanel'
import { getFusedPredictionCopy } from '../../content/farmerCopy'
import { humidityScale, moistureScale, SOIL_PROFILES, temperatureScale, zoneFor } from '../../content/sensorModel'
import { useFarm } from '../../farm/FarmContext'

export default function FarmerDashboard() {
  const { selectedFarmId, selectedFarm, isLoading: farmsLoading, hasFarms } = useFarm()
  const { data: status = null } = useFarmStatus(selectedFarmId)
  const { data: readings, isLoading: readingsLoading } = useLatestReadings(selectedFarmId)
  const { data: alerts = [] } = useAlerts(selectedFarmId)
  const { data: history = [] } = useFarmHistory(selectedFarmId)
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

      {readings && (
        <section aria-labelledby="field-readings-title" className="flex flex-col gap-3">
          <h2 id="field-readings-title" className="m-0 text-[21px] font-bold text-ink">
            Field readings
          </h2>
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

      {status?.has_data !== false && (
        <section className="flex flex-col gap-3" aria-labelledby="alerts-title">
          <h2 id="alerts-title" className="m-0 text-[21px] font-bold text-ink">
            Alerts
          </h2>
          {alerts.length > 0 ? (
            <div className="flex flex-col gap-3">
              {alerts.map((alert) => (
                <AlertCard key={alert.alert_id} alert={alert} />
              ))}
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
