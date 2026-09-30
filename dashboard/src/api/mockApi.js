// Mock data shapes mirror db/schema.sql field names exactly

export function getFarmStatus(farmId) {
  return Promise.resolve({
    farm_id: farmId,
    farm_name: 'Plot 1 - North Field',
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
      severity: 'warning',
      status: 'confirmed',
      message: 'Too much water in the soil. Moisture is high over 3 readings.',
      plain_summary: 'Soil moisture is too high.',
      created_at: new Date(Date.now() - 3600000).toISOString()
    },
    {
      alert_id: 'mock-alert-2',
      farm_id: farmId,
      severity: 'critical',
      status: 'uncertain',
      message: 'Photo unclear. Could not confirm leaf condition.',
      plain_summary: 'Photo was unclear.',
      created_at: new Date(Date.now() - 86400000).toISOString()
    },
    {
      alert_id: 'mock-alert-3',
      farm_id: farmId,
      severity: 'warning',
      status: 'out_of_scope',
      message: 'Unrecognized condition. Leaf pattern does not match supported fungal diseases.',
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

// ── New mock functions ────────────────────────────────────────────────────────

export function login({ phone, password }) {
  // Mock: +254712000001 is the farmer and +254712000002 is the admin.
  if (phone === '+254712000002' && password === 'admin123') {
    // Mock JWT payload for admin (base64url encoded JSON)
    // Header.Payload.Signature. Payload: { sub: 'admin-1', role: 'admin', exp: far future }
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).replace(/=/g, '')
    const payload = btoa(JSON.stringify({ sub: 'admin-1', role: 'admin', farm_id: null, exp: 9999999999 })).replace(/=/g, '')
    return Promise.resolve({ access_token: `${header}.${payload}.mocksig` })
  }
  if (phone === '+254712000001' && password === 'farmer123') {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).replace(/=/g, '')
    const payload = btoa(JSON.stringify({ sub: 'farmer-1', role: 'farmer', farm_id: 'mock-farm-1', exp: 9999999999 })).replace(/=/g, '')
    return Promise.resolve({ access_token: `${header}.${payload}.mocksig` })
  }
  return Promise.reject(new Error('Phone number or password is incorrect'))
}

export function register({ name, phone, password }) {
  return new Promise((resolve, reject) => {
    if (!name || !phone || !password) {
      return reject(new Error('All fields are required'))
    }
    setTimeout(() => resolve({ success: true, message: 'Account created' }), 400)
  })
}

export function getFarmerFarm(farmerId) {
  if (farmerId === 'farmer-1') {
    return Promise.resolve({
      farm_id: 'mock-farm-1',
      farmer_id: 'farmer-1',
      farm_name: 'Plot 1 - North Field',
      location: 'Eldoret, Kenya',
      soil_type: 'sandy_loam'
    })
  }
  // No farm found → return null (used to detect onboarding needed)
  return Promise.resolve(null)
}

export function createFarm({ farmerId, farmName, location, soilType }) {
  return Promise.resolve({
    farm_id: `farm-${Date.now()}`,
    farmer_id: farmerId,
    farm_name: farmName,
    location,
    soil_type: soilType,
    created_at: new Date().toISOString()
  })
}

export function submitCheckin(formData) {
  // Simulates the multi-model inference pipeline
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        prediction_id: `pred-${Date.now()}`,
        farm_id: 'mock-farm-1',
        status: 'confirmed',
        disease_label: 'northern_leaf_blight',
        disease_confidence: 0.87,
        severity_level: 'warning',
        fused_prediction: 'northern_leaf_blight',
        nutrient_status: 'nitrogen_deficiency',
        sensor_conditions: {
          temperature_c: 24.5,
          humidity_pct: 68,
          soil_moisture_pct: 42,
          leaf_wetness: false
        },
        recommendation: 'Apply a foliar fungicide containing propiconazole. Improve field drainage to reduce humidity around the canopy.',
        created_at: new Date().toISOString()
      })
    }, 1200)
  })
}

export function getPredictionById(predictionId) {
  return Promise.resolve({
    prediction_id: predictionId,
    farm_id: 'mock-farm-1',
    status: 'confirmed',
    disease_label: 'northern_leaf_blight',
    disease_confidence: 0.87,
    severity_level: 'warning',
    fused_prediction: 'northern_leaf_blight',
    nutrient_status: 'nitrogen_deficiency',
    nutrient_confidence: 0.76,
    sensor_conditions: {
      temperature_c: 24.5,
      humidity_pct: 68,
      soil_moisture_pct: 42,
      leaf_wetness: false
    },
    recommendation: 'Apply a foliar fungicide containing propiconazole. Improve field drainage to reduce humidity around the canopy.',
    created_at: new Date(Date.now() - 600000).toISOString()
  })
}

export function getAllAlerts() {
  return Promise.resolve([
    { alert_id: 'a-1', farm_id: 'farm-1', farm_name: 'Demo Farm A', severity: 'warning', status: 'confirmed', plain_summary: 'Soil moisture is too high.', created_at: new Date(Date.now() - 3600000).toISOString() },
    { alert_id: 'a-2', farm_id: 'farm-2', farm_name: 'Demo Farm B', severity: 'critical', status: 'uncertain', plain_summary: 'Photo was unclear.', created_at: new Date(Date.now() - 86400000).toISOString() },
    { alert_id: 'a-3', farm_id: 'farm-3', farm_name: 'Demo Farm C', severity: 'critical', status: 'confirmed', plain_summary: 'Leaf blight detected. High confidence.', created_at: new Date(Date.now() - 172800000).toISOString() }
  ])
}

export function getAllUsers() {
  return Promise.resolve([
    { user_id: 'farmer-1', name: 'Joyce Wanjiru', phone: '+254712000001', role: 'farmer', farm_id: 'mock-farm-1', farm_name: 'Plot 1 - North Field', registered_at: '2026-09-01T08:00:00Z' },
    { user_id: 'farmer-2', name: 'Peter Otieno', phone: '+254712000003', role: 'farmer', farm_id: 'farm-2', farm_name: 'Demo Farm B', registered_at: '2026-09-05T10:30:00Z' },
    { user_id: 'admin-1', name: 'Admin User', phone: '+254712000002', role: 'admin', farm_id: null, farm_name: null, registered_at: '2026-08-20T09:00:00Z' }
  ])
}

export function getModelVersions() {
  return Promise.resolve([
    { model_type: 'triage', version: 'v1.2.0', accuracy: 0.94, f1_score: 0.92, active: true, deployed_at: '2026-09-10T00:00:00Z' },
    { model_type: 'disease', version: 'v2.1.0', accuracy: 0.89, f1_score: 0.87, active: true, deployed_at: '2026-09-12T00:00:00Z' },
    { model_type: 'nutrient', version: 'v1.0.3', accuracy: 0.82, f1_score: 0.80, active: true, deployed_at: '2026-09-08T00:00:00Z' },
    { model_type: 'sensor', version: 'v1.1.1', accuracy: 0.91, f1_score: 0.90, active: true, deployed_at: '2026-09-09T00:00:00Z' }
  ])
}

export function switchModelVersion(modelType, versionId) {
  return Promise.resolve({ success: true, model_type: modelType, version_id: versionId })
}

export function getFeedbackList(filterNotAccurate = false) {
  const all = [
    { feedback_id: 'fb-1', prediction_id: 'pred-001', farmer_id: 'farmer-1', farmer_confirmed: true, comment: '', timestamp: new Date(Date.now() - 7200000).toISOString() },
    { feedback_id: 'fb-2', prediction_id: 'pred-002', farmer_id: 'farmer-2', farmer_confirmed: false, comment: 'The severity seemed higher than shown.', timestamp: new Date(Date.now() - 86400000).toISOString() },
    { feedback_id: 'fb-3', prediction_id: 'pred-003', farmer_id: 'farmer-1', farmer_confirmed: false, comment: 'Healthy crop was flagged as diseased.', timestamp: new Date(Date.now() - 172800000).toISOString() },
    { feedback_id: 'fb-4', prediction_id: 'pred-004', farmer_id: 'farmer-2', farmer_confirmed: true, comment: '', timestamp: new Date(Date.now() - 259200000).toISOString() }
  ]
  return Promise.resolve(filterNotAccurate ? all.filter(f => !f.farmer_confirmed) : all)
}

export function triggerRetrain(modelType) {
  return Promise.resolve({
    job_id: `job-${Date.now()}`,
    model_type: modelType,
    status: 'pending',
    created_at: new Date().toISOString()
  })
}

export function getRetrainingJobs() {
  return Promise.resolve([
    {
      job_id: 'job-001',
      model_type: 'disease',
      status: 'deployed',
      old_accuracy: 0.85,
      new_accuracy: 0.89,
      old_f1: 0.83,
      new_f1: 0.87,
      passed_validation: true,
      deployed: true,
      created_at: new Date(Date.now() - 604800000).toISOString(),
      completed_at: new Date(Date.now() - 601200000).toISOString()
    },
    {
      job_id: 'job-002',
      model_type: 'nutrient',
      status: 'failed_validation',
      old_accuracy: 0.82,
      new_accuracy: 0.79,
      old_f1: 0.80,
      new_f1: 0.76,
      passed_validation: false,
      deployed: false,
      created_at: new Date(Date.now() - 259200000).toISOString(),
      completed_at: new Date(Date.now() - 255600000).toISOString()
    }
  ])
}

export function getSmsLog() {
  return Promise.resolve([
    { sms_id: 'sms-1', recipient: '+254712000001', message: 'Warning: soil moisture is critically high. Check your drainage.', status: 'delivered', sent_at: new Date(Date.now() - 3600000).toISOString() },
    { sms_id: 'sms-2', recipient: '+254712000003', message: 'Alert: northern leaf blight detected with high confidence.', status: 'delivered', sent_at: new Date(Date.now() - 86400000).toISOString() },
    { sms_id: 'sms-3', recipient: '+254712000001', message: 'Your last photo was unclear. Please retake in good lighting.', status: 'failed', sent_at: new Date(Date.now() - 172800000).toISOString() }
  ])
}