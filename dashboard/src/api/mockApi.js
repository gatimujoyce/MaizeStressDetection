// Mock data shapes mirror db/schema.sql field names exactly

export function getFarmStatus(farmId) {
  return Promise.resolve({
    farm_id: farmId,
    fused_prediction: 'drought_stress',
    disease_prediction: 'healthy',
    sensor_prediction: 'drought_stress',
    severity_level: 'medium',
    status: 'confirmed', // 'confirmed' | 'uncertain' | 'out_of_scope'
    created_at: new Date().toISOString()
  })
}

export function getAlerts(farmId) {
  return Promise.resolve([
    {
      alert_id: 'mock-1',
      farm_id: farmId,
      severity: 'medium',
      message: 'Drought stress detected — soil moisture trending down over 3 readings.',
      sms_sent: true,
      created_at: new Date().toISOString()
    }
  ])
}

export function getAllFarms() {
  return Promise.resolve([
    { farm_id: 'mock-farm-1', name: 'Demo Farm A', fused_prediction: 'normal', severity_level: 'low' },
    { farm_id: 'mock-farm-2', name: 'Demo Farm B', fused_prediction: 'waterlogging_risk', severity_level: 'high' }
  ])
}

export function getSystemHealth() {
  return Promise.resolve({ total_farms: 2, active_alerts: 1, last_sync: new Date().toISOString() })
}