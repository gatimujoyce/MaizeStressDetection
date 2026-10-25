// Mock data shapes mirror db/schema.sql field names exactly
import { mockReading, SOIL_PROFILES } from '../content/sensorModel'

const SEEDED_FARMER_ID = 'farmer-1'
const FIRST_FARM_ID = 'mock-farm-1'
const SECOND_FARM_ID = 'mock-farm-2'
const PERSISTED_FARMS_KEY = 'msm_mock_farms'
const PERSISTED_CHECKINS_KEY = 'msm_mock_checkins'

const seededFarms = {
  [SEEDED_FARMER_ID]: [
    {
      farm_id: FIRST_FARM_ID,
      farmer_id: SEEDED_FARMER_ID,
      farm_name: 'Plot 1 - North Field',
      location: 'Eldoret, Kenya',
      soil_type: 'sandy_loam'
    },
    {
      farm_id: SECOND_FARM_ID,
      farmer_id: SEEDED_FARMER_ID,
      farm_name: 'Plot 2 - South Field',
      location: 'Eldoret, Kenya',
      soil_type: 'loam'
    }
  ]
}

function readPersistedFarms() {
  try {
    const stored = localStorage.getItem(PERSISTED_FARMS_KEY)
    if (!stored) return []
    const farms = JSON.parse(stored)
    return Array.isArray(farms) ? farms : []
  } catch (error) {
    console.error('Unable to read saved mock farms', error)
    return []
  }
}

function persistFarms(farms) {
  try {
    localStorage.setItem(PERSISTED_FARMS_KEY, JSON.stringify(farms))
  } catch (error) {
    throw new Error('Unable to save mock farms to local storage', { cause: error })
  }
}

function readSavedCheckins() {
  try {
    const saved = localStorage.getItem(PERSISTED_CHECKINS_KEY)
    if (!saved) return {}
    const checkins = JSON.parse(saved)
    return checkins && typeof checkins === 'object' && !Array.isArray(checkins) ? checkins : {}
  } catch (error) {
    console.error('Unable to read saved mock check-ins', error)
    return {}
  }
}

function persistCheckins(checkins) {
  try {
    localStorage.setItem(PERSISTED_CHECKINS_KEY, JSON.stringify(checkins))
  } catch (error) {
    throw new Error('Unable to save mock check-in to local storage', { cause: error })
  }
}

function farmsForFarmer(farmerId) {
  const seeded = seededFarms[farmerId] ?? []
  const persisted = readPersistedFarms().filter((farm) => farm?.farmer_id === farmerId)
  const byId = new Map(seeded.map((farm) => [farm.farm_id, farm]))
  for (const farm of persisted) {
    if (farm?.farm_id && !byId.has(farm.farm_id)) byId.set(farm.farm_id, farm)
  }
  return [...byId.values()]
}

export function getFarmStatus(farmId) {
  if (farmId === FIRST_FARM_ID) {
    return Promise.resolve({
      farm_id: farmId,
      farm_name: 'Plot 1 - North Field',
      fused_prediction: 'waterlogging_risk',
      disease_prediction: 'healthy',
      sensor_prediction: 'waterlogging_risk',
      severity_level: 'warning', // 'healthy' | 'warning' | 'critical'
      status: 'confirmed', // 'confirmed' | 'uncertain' | 'out_of_scope'
      nutrient_status: 'nitrogen_deficiency', // Separate prediction pathway
      has_data: true,
      created_at: new Date().toISOString()
    })
  }

  if (farmId === SECOND_FARM_ID) {
    return Promise.resolve({
      farm_id: farmId,
      farm_name: 'Plot 2 - South Field',
      fused_prediction: 'healthy',
      disease_prediction: 'healthy',
      sensor_prediction: 'healthy',
      severity_level: 'healthy',
      status: 'confirmed',
      nutrient_status: 'healthy',
      has_data: true,
      created_at: new Date().toISOString()
    })
  }

  const farm = farmsForFarmer(SEEDED_FARMER_ID).find((item) => item?.farm_id === farmId)
  const checkin = readSavedCheckins()[farmId]
  if (checkin?.prediction) {
    const prediction = checkin.prediction
    return Promise.resolve({
      farm_id: farmId,
      farm_name: farm?.farm_name ?? 'Your field',
      has_data: true,
      fused_prediction: prediction.fused_prediction,
      sensor_prediction: prediction.sensor_prediction,
      severity_level: prediction.severity_level,
      nutrient_status: prediction.nutrient_status,
      created_at: checkin.created_at ?? prediction.created_at,
    })
  }

  return Promise.resolve({
    farm_id: farmId,
    farm_name: farm?.farm_name ?? 'Your field',
    has_data: false
  })
}

export async function getLatestReadings(farmId) {
  const status = await getFarmStatus(farmId)
  if (status.has_data === false) return null

  const farm = farmsForFarmer(SEEDED_FARMER_ID).find((item) => item?.farm_id === farmId)
  const soilType = SOIL_PROFILES[farm?.soil_type] ? farm.soil_type : 'loam'
  const stressClasses = ['normal', 'drought_stress', 'heat_stress', 'waterlogging_risk']
  const sensorClass = stressClasses.includes(status.sensor_prediction)
    ? status.sensor_prediction
    : 'normal'

  return {
    ...mockReading(soilType, sensorClass),
    recorded_at: status.created_at,
  }
}

export function getAlerts(farmId) {
  if (farmId !== FIRST_FARM_ID) {
    if (farmId === SECOND_FARM_ID) return Promise.resolve([])
    const prediction = readSavedCheckins()[farmId]?.prediction
    if (!prediction || prediction.severity_level === 'healthy') return Promise.resolve([])
    return Promise.resolve([{
      alert_id: prediction.prediction_id,
      farm_id: farmId,
      severity: prediction.severity_level,
      status: prediction.status,
      message: prediction.recommendation,
      plain_summary: `${prediction.disease_label?.replace(/_/g, ' ') || prediction.fused_prediction?.replace(/_/g, ' ') || 'Stress'} detected.`,
      created_at: prediction.created_at
    }])
  }

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

export function getFarmHistory(farmId) {
  if (farmId === SECOND_FARM_ID) {
    return Promise.resolve([
      { date: 'Wk 1', severity: 'healthy', score: 1, stage: 'Vegetative (V3)' },
      { date: 'Wk 2', severity: 'healthy', score: 1, stage: 'Vegetative (V6)' },
      { date: 'Wk 3', severity: 'healthy', score: 1, stage: 'Tasseling (VT)' },
      { date: 'Wk 4', severity: 'healthy', score: 1, stage: 'Silking (R1)' }
    ])
  }
  if (farmId !== FIRST_FARM_ID) {
    const prediction = readSavedCheckins()[farmId]?.prediction
    if (!prediction) return Promise.resolve([])
    return Promise.resolve([{
      date: new Date(prediction.created_at).toLocaleDateString(),
      severity: prediction.severity_level,
      score: prediction.severity_level === 'healthy' ? 1 : prediction.severity_level === 'critical' ? 3 : 2,
      stage: 'Most recent check-in'
    }])
  }

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
  return getFarmerFarms(farmerId).then((farms) => farms[0] ?? null)
}

export function getFarmerFarms(farmerId) {
  try {
    return Promise.resolve(farmsForFarmer(farmerId))
  } catch (error) {
    console.error('Unable to load mock farms for farmer', error)
    return Promise.resolve([])
  }
}

export function createFarm({
  farmerId,
  farmName,
  location,
  soilType,
  sizeAcres,
  county,
  waterSource,
  plantingDate,
  seedVariety
}) {
  const farmId = `farm-${Date.now()}`
  const farm = {
    id: farmId,
    farm_id: farmId,
    farmer_id: farmerId,
    farm_name: farmName,
    location,
    soil_type: soilType,
    sizeAcres,
    county,
    waterSource,
    plantingDate,
    seedVariety,
    created_at: new Date().toISOString()
  }
  const farms = farmsForFarmer(farmerId)
  farms.push(farm)
  const createdFarms = farms.filter(
    (item) => !seededFarms[farmerId]?.some((seed) => seed.farm_id === item.farm_id)
  )
  persistFarms([
    ...readPersistedFarms().filter((item) => item?.farmer_id !== farmerId),
    ...createdFarms
  ])
  return Promise.resolve(farm)
}

export function submitCheckin(input) {
  // Simulates the multi-model inference pipeline
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const farmId = input instanceof FormData
        ? input.get('farm_id') || FIRST_FARM_ID
        : input?.farm_id || FIRST_FARM_ID
      const farm = farmsForFarmer(SEEDED_FARMER_ID).find((item) => item?.farm_id === farmId)
      const sensorPrediction = farmId === FIRST_FARM_ID ? 'waterlogging_risk' : 'normal'
      const reading = mockReading(farm?.soil_type, sensorPrediction)
      const createdAt = new Date().toISOString()
      const prediction = {
        prediction_id: `pred-${Date.now()}`,
        farm_id: farmId,
        status: 'confirmed',
        disease_label: 'northern_leaf_blight',
        disease_confidence: 0.87,
        severity_level: 'warning',
        fused_prediction: 'northern_leaf_blight',
        nutrient_status: 'nitrogen_deficiency',
        sensor_prediction: sensorPrediction,
        sensor_conditions: {
          temperature_c: reading.temperature,
          humidity_pct: reading.humidity,
          soil_moisture_pct: reading.soil_moisture,
          leaf_wetness: reading.leaf_wetness < 3,
        },
        recommendation: 'Apply a foliar fungicide containing propiconazole. Improve field drainage to reduce humidity around the canopy.',
        created_at: createdAt
      }
      try {
        persistCheckins({
          ...readSavedCheckins(),
          [farmId]: { prediction, created_at: createdAt }
        })
        resolve(prediction)
      } catch (error) {
        reject(error)
      }
    }, 1200)
  })
}

export function getPredictionById(predictionId) {
  const savedPrediction = Object.values(readSavedCheckins())
    .map((checkin) => checkin?.prediction)
    .find((prediction) => prediction?.prediction_id === predictionId)
  if (savedPrediction) return Promise.resolve(savedPrediction)

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
    sensor_prediction: 'waterlogging_risk',
    sensor_conditions: {
      temperature_c: 22,
      humidity_pct: 85,
      soil_moisture_pct: 25,
      leaf_wetness: true,
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