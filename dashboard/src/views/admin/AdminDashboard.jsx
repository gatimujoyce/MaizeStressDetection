import { useEffect, useState } from 'react'
import { getAllFarms, getSystemHealth } from '../../api/mockApi'

export default function AdminDashboard() {
  const [farms, setFarms] = useState([])
  const [health, setHealth] = useState(null)

  useEffect(() => {
    getAllFarms().then(setFarms)
    getSystemHealth().then(setHealth)
  }, [])

  return (
    <div>
      <h1>Admin Dashboard</h1>

      <section style={{ marginBottom: '2rem' }}>
        <h2>System Health</h2>
        {health ? (
          <div style={{ display: 'flex', gap: '2rem' }}>
            <div><strong>Total Farms:</strong> {health.total_farms}</div>
            <div><strong>Active Alerts:</strong> {health.active_alerts}</div>
            <div><strong>Last Sync:</strong> {new Date(health.last_sync).toLocaleString()}</div>
          </div>
        ) : (
          <p>Loading system health...</p>
        )}
      </section>

      <section>
        <h2>All Managed Farms</h2>
        {farms.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ccc' }}>
                <th style={{ padding: '0.5rem' }}>Farm ID</th>
                <th style={{ padding: '0.5rem' }}>Name</th>
                <th style={{ padding: '0.5rem' }}>Prediction</th>
                <th style={{ padding: '0.5rem' }}>Severity</th>
              </tr>
            </thead>
            <tbody>
              {farms.map(f => (
                <tr key={f.farm_id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '0.5rem' }}>{f.farm_id}</td>
                  <td style={{ padding: '0.5rem' }}>{f.name}</td>
                  <td style={{ padding: '0.5rem' }}>{f.fused_prediction}</td>
                  <td style={{ padding: '0.5rem' }}>{f.severity_level}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>Loading farms...</p>
        )}
      </section>
    </div>
  )
}