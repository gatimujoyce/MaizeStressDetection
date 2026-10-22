// Single data-access layer.
// Feature flag: VITE_USE_MOCK_API=true → calls mockApi.js
//               VITE_USE_MOCK_API=false → calls real backend via httpClient.js
import * as mock from './mockApi'
import { httpClient } from './httpClient'
import { fusedPredictionCopy } from '../content/farmerCopy'

const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true'
const realApi = {
    status: true,
    farmerFarm: false,
    farms: false,
    readings: false,
    history: false,
    alerts: false,
    allAlerts: false,
    checkin: false,
    prediction: false,
    feedback: false,
    systemHealth: false,
    users: false,
    models: false,
    retrain: false,
    retrainingJobs: false,
    smsLog: false,
}

const predictionCopyKeys = Object.keys(fusedPredictionCopy)

function adaptFarmStatus(response) {
    const prediction = response.latest_prediction
    if (!prediction) {
        return {
            farm_id: response.farm_id,
            has_data: false,
        }
    }

    const severity = prediction.severity?.toLowerCase()
    const severityLevel = {
        low: 'healthy',
        medium: 'warning',
        high: 'critical',
        inconclusive: 'neutral',
    }[severity] ?? 'neutral'

    const toCopyKey = (label) => {
        if (typeof label !== 'string') return null
        const normalized = label.toLowerCase().trim().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '')
        if (normalized === 'normal') return 'healthy'
        return predictionCopyKeys.includes(normalized) ? normalized : null
    }

    const diseaseKey = toCopyKey(prediction.disease_label)
    const sensorKey = toCopyKey(prediction.sensor_label)
    const isHealthyDisease = diseaseKey === 'healthy'
    const isOutOfScope = prediction.triage_result?.toLowerCase() === 'out_of_scope'
    const labelKey = severity === 'low'
        ? 'healthy'
        : isOutOfScope
            ? diseaseKey ?? sensorKey
            : diseaseKey && !isHealthyDisease
            ? diseaseKey
            : sensorKey ?? diseaseKey
    const fusedPrediction = labelKey ?? (severity === 'low' ? 'healthy' : 'leaf_blight')

    return {
        farm_id: response.farm_id,
        has_data: true,
        fused_prediction: fusedPrediction,
        severity_level: severityLevel,
        created_at: prediction.created_at,
        ...(prediction.nutrient_label != null ? { nutrient_status: prediction.nutrient_label } : {}),
    }
}

const shouldUseMock = (endpoint) => USE_MOCK && !realApi[endpoint]

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (credentials) =>
    httpClient.post(
        '/auth/login',
        new URLSearchParams({ username: credentials.phone, password: credentials.password }),
    )

export const register = (data) =>
    httpClient.post('/auth/register', data)

export const getCurrentUser = () =>
    httpClient.get('/auth/me')

// ── Farms ─────────────────────────────────────────────────────────────────────
export const getFarmerFarm = (farmerId) =>
    shouldUseMock('farmerFarm') ? mock.getFarmerFarm(farmerId) : httpClient.get(`/farms/farmer/${farmerId}`)

const mapFarmResponse = (farm) => ({
    ...farm,
    farm_id: farm.id,
    farmer_id: farm.user_id,
    farm_name: farm.name,
    sizeAcres: farm.size_acres,
    county: farm.location,
    plantingDate: farm.planting_date,
    waterSource: farm.water_source,
    seedVariety: farm.seed_variety,
})

export const getFarmerFarms = () =>
    httpClient.get('/farms').then((farms) => farms.map(mapFarmResponse))

export const createFarm = (data) =>
    httpClient.post('/farms', {
        name: data.farmName,
        location: data.county,
        soil_type: data.soilType,
        size_acres: data.sizeAcres,
        planting_date: data.plantingDate,
        water_source: data.waterSource,
        seed_variety: data.seedVariety,
    }).then(mapFarmResponse)

export const getFarmStatus = (farmId) =>
    shouldUseMock('status')
        ? mock.getFarmStatus(farmId)
        : httpClient.get(`/farms/${farmId}/status`).then(adaptFarmStatus)

export const getLatestReadings = (farmId) =>
    shouldUseMock('readings')
        ? mock.getLatestReadings(farmId)
        // path to confirm at integration
        : httpClient.get(`/farms/${farmId}/readings/latest`)

export const getFarmHistory = (farmId, days = 30) =>
    shouldUseMock('history') ? mock.getFarmHistory(farmId, days) : httpClient.get(`/farms/${farmId}/history?days=${days}`)

export const getAllFarms = () =>
    shouldUseMock('farms') ? mock.getAllFarms() : httpClient.get('/farms')

// ── Check-ins / Predictions ───────────────────────────────────────────────────
export const submitCheckin = (formData) =>
    shouldUseMock('checkin') ? mock.submitCheckin(formData) : httpClient.post('/checkins', formData)

export const getPredictionById = (predictionId) =>
    shouldUseMock('prediction') ? mock.getPredictionById(predictionId) : httpClient.get(`/predictions/${predictionId}`)

export const getAlerts = (farmId) =>
    shouldUseMock('alerts') ? mock.getAlerts(farmId) : httpClient.get(`/farms/${farmId}/alerts`)

export const getAllAlerts = () =>
    shouldUseMock('allAlerts') ? mock.getAllAlerts() : httpClient.get('/alerts')

// ── Feedback ──────────────────────────────────────────────────────────────────
export const confirmPrediction = (alertId, farmerId, confirmed, comment = '') =>
    shouldUseMock('feedback')
        ? mock.confirmPrediction(alertId, farmerId, confirmed, comment)
        : httpClient.post('/feedback', { prediction_id: alertId, farmer_id: farmerId, farmer_confirmed: confirmed, comment })

export const getFeedbackList = (filterNotAccurate = false) =>
    shouldUseMock('feedback') ? mock.getFeedbackList(filterNotAccurate) : httpClient.get(`/feedback${filterNotAccurate ? '?not_accurate=true' : ''}`)

// ── Admin / System ────────────────────────────────────────────────────────────
export const getSystemHealth = () =>
    shouldUseMock('systemHealth') ? mock.getSystemHealth() : httpClient.get('/system/health')

export const getAllUsers = () =>
    shouldUseMock('users') ? mock.getAllUsers() : httpClient.get('/users')

export const getModelVersions = () =>
    shouldUseMock('models') ? mock.getModelVersions() : httpClient.get('/models')

export const switchModelVersion = (modelType, versionId) =>
    shouldUseMock('models')
        ? mock.switchModelVersion(modelType, versionId)
        : httpClient.patch(`/models/${modelType}/activate`, { version_id: versionId })

export const triggerRetrain = (modelType) =>
    shouldUseMock('retrain') ? mock.triggerRetrain(modelType) : httpClient.post('/retrain', { model_type: modelType })

export const getRetrainingJobs = () =>
    shouldUseMock('retrainingJobs') ? mock.getRetrainingJobs() : httpClient.get('/retrain/jobs')

export const getSmsLog = () =>
    shouldUseMock('smsLog') ? mock.getSmsLog() : httpClient.get('/sms/log')
