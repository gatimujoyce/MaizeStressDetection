// Mock data shapes mirror db/schema.sql field names exactly

export function getFarmStatus(farmId) {
  return Promise.resolve({
    farm_id: farmId,
    farm_name: 'Plot 1 — North Field',
    fused_prediction: 'drought_stress',
    disease_prediction: 'healthy',
    sensor_prediction: 'drought_stress',
    severity_level: 'warning', // 'healthy' | 'warning' | 'critical'
    status: 'confirmed', // 'confirmed' | 'uncertain' | 'out_of_scope'
    nutrient_status: 'nitrogen_deficiency', // Separate prediction pathway
    created_at: new Date().toISOString()
  })
}

export function getAlerts(farmId) {
  return Promise.resolve([
    {
      alert_id: 'mock-alert-1',
      farm_id: farmId,
      severity: 'warning', // 'healthy' | 'warning' | 'critical'
      status: 'confirmed', // 'confirmed' | 'uncertain' | 'out_of_scope'
      message: 'Too much water in the soil — moisture high over 3 readings.',
      plain_summary: 'Soil moisture is too high.',
      created_at: new Date(Date.now() - 3600000).toISOString()
    },
    {
      alert_id: 'mock-alert-2',
      farm_id: farmId,
      severity: 'critical',
      status: 'uncertain',
      message: 'Photo unclear — could not confirm leaf condition.',
      plain_summary: 'Photo was unclear.',
      created_at: new Date(Date.now() - 86400000).toISOString()
    },
    {
      alert_id: 'mock-alert-3',
      farm_id: farmId,
      severity: 'warning',
      status: 'out_of_scope',
      message: 'Unrecognized condition — leaf pattern does not match supported fungal diseases.',
      plain_summary: 'Condition not recognized.',
      created_at: new Date(Date.now() - 172800000).toISOString()
    }
  ])
}

export function confirmPrediction(alertId, farmerId, confirmed, comment = '') {
  return Promise.resolve({
    feedback_id: `fb-${Date.now()}`,
    prediction_id: alertId,
    farmer_id: farmerId,
    farmer_confirmed: confirmed,
    comment: comment,
    timestamp: new Date().toISOString()
  })
}

export function getFarmHistory(farmId, days = 30) {
  const history = [
    { date: 'Wk 1', severity: 'healthy', score: 1, stage: 'Vegetative (V3)' },
    { date: 'Wk 2', severity: 'healthy', score: 1, stage: 'Vegetative (V6)' },
    { date: 'Wk 3', severity: 'warning', score: 2, stage: 'Tasseling (VT)' },
    { date: 'Wk 4', severity: 'warning', score: 2, stage: 'Silking (R1)' }
  ]
  return Promise.resolve(history)
}

export function getAllFarms() {
  return Promise.resolve([
    { farm_id: 'farm-1', name: 'Demo Farm A', fused_prediction: 'healthy', severity_level: 'healthy', last_checkin: '10 mins ago' },
    { farm_id: 'farm-2', name: 'Demo Farm B', fused_prediction: 'waterlogging_risk', severity_level: 'warning', last_checkin: '1 hour ago' },
    { farm_id: 'farm-3', name: 'Demo Farm C', fused_prediction: 'leaf_blight', severity_level: 'critical', last_checkin: '3 hours ago' }
  ])
}

export function getSystemHealth() {
  return Promise.resolve({ total_farms: 3, active_alerts: 2, last_sync: new Date().toISOString() })
}