import { useEffect, useState } from 'react'
import { getFarmStatus, getAlerts } from '../../api/mockApi'

export default function FarmerDashboard() {
  const [status, setStatus] = useState(null)
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    getFarmStatus('mock-farm-1').then(setStatus)
    getAlerts('mock-farm-1').then(setAlerts)
  }, [])

  return (
    <div>
      <h1>Farmer Dashboard</h1>
      
      <section style={{ marginBottom: '2rem' }}>
        <h2>Farm Status</h2>
        {status ? (
          <div style={{ padding: '1rem', border: '1px solid #ccc', borderRadius: '4px' }}>
            <p><strong>Farm ID:</strong> {status.farm_id}</p>
            <p><strong>Fused Prediction:</strong> {status.fused_prediction}</p>
            <p><strong>Severity Level:</strong> {status.severity_level}</p>
            <p><strong>Status:</strong> {status.status}</p>
          </div>
        ) : (
          <p>Loading farm status...</p>
        )}
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2>Recent Alerts</h2>
        {alerts.length > 0 ? (
          <ul>
            {alerts.map(a => (
              <li key={a.alert_id} style={{ marginBottom: '0.5rem' }}>
                <strong>[{a.severity.toUpperCase()}]</strong> {a.message}
              </li>
            ))}
          </ul>
        ) : (
          <p>No active alerts.</p>
        )}
      </section>

      <section>
        <button disabled style={{ padding: '0.5rem 1rem', opacity: 0.6 }}>
          Upload Leaf Photo (coming soon)
        </button>
      </section>
    </div>
  )
}