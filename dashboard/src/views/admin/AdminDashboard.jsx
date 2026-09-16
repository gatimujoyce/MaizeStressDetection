import React, { useEffect, useState } from 'react'
import { getAllFarms, getSystemHealth } from '../../api/mockApi'
import StatCard from '../../components/StatCard'
import FarmTable from '../../components/FarmTable'

export default function AdminDashboard() {
  const [farms, setFarms] = useState([])
  const [health, setHealth] = useState(null)

  useEffect(() => {
    getAllFarms().then(setFarms)
    getSystemHealth().then(setHealth)
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ margin: 0, fontSize: '1.75rem' }}>Admin Monitoring Portal</h1>
        <p style={{ color: 'var(--color-text-secondary)', margin: '0.25rem 0 0 0' }}>
          Overview across all registered farm locations.
        </p>
      </div>

      {/* System Health Cards */}
      <section style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <StatCard
          label="Total Managed Farms"
          value={health ? health.total_farms : '...'}
          status="neutral"
          icon="🚜"
        />
        <StatCard
          label="Active Alerts"
          value={health ? health.active_alerts : '...'}
          status={health?.active_alerts > 0 ? 'warning' : 'healthy'}
          icon="🚨"
        />
        <StatCard
          label="Last System Sync"
          value={health ? new Date(health.last_sync).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '...'}
          status="neutral"
          icon="🔄"
        />
      </section>

      {/* All Farms Table */}
      <section>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '0.75rem' }}>All Farms Overview</h2>
        <FarmTable farms={farms} />
      </section>
    </div>
  )
}