import React, { useEffect, useState } from 'react'
import { getFarmStatus, getAlerts, getFarmHistory } from '../../api/mockApi'
import StatCard from '../../components/StatCard'
import FeedbackControl from '../../components/FeedbackControl'
import TrendChart from '../../components/TrendChart'
import { WarningIcon, InfoIcon, ErrorIcon } from '../../components/Icons'

export default function FarmerDashboard() {
  const [status, setStatus] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [history, setHistory] = useState([])
  const [isOffline, setIsOffline] = useState(!navigator.onLine)

  useEffect(() => {
    getFarmStatus('mock-farm-1').then(setStatus)
    getAlerts('mock-farm-1').then(setAlerts)
    getFarmHistory('mock-farm-1').then(setHistory)

    const handleOnline = () => setIsOffline(false)
    const handleOffline = () => setIsOffline(true)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const renderAlertCard = (alert) => {
    if (alert.status === 'uncertain') {
      return (
        <div key={alert.alert_id} style={{
          backgroundColor: 'var(--color-neutral-bg)',
          border: '1px solid var(--color-border)',
          borderRadius: '2px',
          padding: '1rem',
          marginBottom: '0.75rem'
        }}>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', color: 'var(--color-neutral-text)', fontWeight: '600' }}>
            <InfoIcon color="var(--color-neutral-text)" size={16} />
            <span>Inconclusive Image Analysis</span>
          </div>
          <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
            Image resolution or lighting was insufficient to determine leaf condition. Upload a high-resolution photo taken in daylight.
          </p>
        </div>
      )
    }

    if (alert.status === 'out_of_scope') {
      return (
        <div key={alert.alert_id} style={{
          backgroundColor: 'var(--color-neutral-bg)',
          border: '1px solid var(--color-border)',
          borderRadius: '2px',
          padding: '1rem',
          marginBottom: '0.75rem'
        }}>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', color: 'var(--color-neutral-text)', fontWeight: '600' }}>
            <InfoIcon color="var(--color-neutral-text)" size={16} />
            <span>Unrecognized Pattern</span>
          </div>
          <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
            Detected symptom parameters do not match registered models. Consult local agronomic extension services.
          </p>
        </div>
      )
    }

    const isCritical = alert.severity === 'critical'
    return (
      <div key={alert.alert_id} style={{
        backgroundColor: isCritical ? 'var(--color-critical-bg)' : 'var(--color-warning-bg)',
        border: '1px solid var(--color-border)',
        borderRadius: '2px',
        padding: '1rem',
        marginBottom: '0.75rem'
      }}>
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          alignItems: 'center',
          color: isCritical ? 'var(--color-critical-text)' : 'var(--color-warning-text)',
          fontWeight: '600'
        }}>
          {isCritical ? <ErrorIcon color="var(--color-critical-text)" /> : <WarningIcon color="var(--color-warning-text)" />}
          <span>{alert.plain_summary}</span>
        </div>
        <p style={{ margin: '0.5rem 0', fontSize: '0.9rem', color: 'var(--color-text-primary)' }}>{alert.message}</p>
        <FeedbackControl alertId={alert.alert_id} />
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {isOffline && (
        <div style={{
          backgroundColor: 'var(--color-neutral-text)',
          color: '#FFFFFF',
          padding: '0.5rem 1rem',
          borderRadius: '2px',
          fontSize: '0.85rem'
        }}>
          Offline mode. Displaying cached field data.
        </div>
      )}

      <div>
        <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {status?.farm_name || 'Plot Status'}
        </span>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Field Monitoring Dashboard</h1>
      </div>

      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <StatCard
          label="Crop Stress"
          value={status ? status.fused_prediction.replace('_', ' ') : 'Loading'}
          status={status?.severity_level || 'neutral'}
          subtext="Derived from leaf imagery and soil telemetry."
        />
        <StatCard
          label="Nutrient Level"
          value={status ? status.nutrient_status.replace('_', ' ') : 'Loading'}
          status="neutral"
          subtext="Assessed via specialized classification model."
        />
      </div>

      <section>
        <h2 style={{ fontSize: '1.1rem', marginBottom: '0.75rem' }}>System Alerts</h2>
        {alerts.length > 0 ? alerts.map(renderAlertCard) : <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>No active alerts recorded.</p>}
      </section>

      <TrendChart history={history} />
    </div>
  )
}