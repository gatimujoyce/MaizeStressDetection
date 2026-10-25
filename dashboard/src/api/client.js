// Single data-access layer.
// Feature flag: VITE_USE_MOCK_API=true → calls mockApi.js
//               VITE_USE_MOCK_API=false → calls real backend via httpClient.js
import * as mock from './mockApi'
import { httpClient } from './httpClient'
import { adaptFarmStatus, adaptPredictionResponse } from './statusAdapter'

const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true'
const realApi = {
    status: true,
    farmerFarm: false,
    farms: false,
    readings: true,
    history: true,
    alerts: true,
    checkin: true,
    prediction: true,
    feedback: false,
    systemHealth: false,
    users: false,
    models: false,
    retrain: false,
    retrainingJobs: false,
    smsLog: false,
}

const shouldUseMock = (endpoint) => USE_MOCK && !realApi[endpoint]

function adaptAlertResponse(alert) {
    const normalizedSeverity = alert.severity?.toLowerCase()
    return {
        ...alert,
        alert_id: alert.id,
        severity: normalizedSeverity === 'high'
            ? 'critical'
            : normalizedSeverity === 'medium'
                ? 'warning'
                : 'neutral',
        severity_label: alert.severity,
    }
}

function adaptReadingResponse(reading) {
    const tileFields = ['soil_moisture', 'temperature', 'humidity']
    const hasValidTileValues = tileFields.every((field) =>
        Number.isFinite(reading?.[field]),
    )
    if (!hasValidTileValues) {
        throw new Error('The server returned incomplete field readings.')
    }
    return reading
}

function adaptFarmHistoryResponse(response) {
    const severityMap = {
        Low: 'healthy',
        Medium: 'warning',
        High: 'critical',
        Inconclusive: 'inconclusive',
    }

    return (response.predictions ?? [])
        .slice()
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .map((prediction) => ({
            id: prediction.id,
            date: new Date(prediction.created_at).toLocaleDateString('en-GB', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
            }),
            severity: severityMap[prediction.severity],
        }))
}

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
        : httpClient.get(`/farms/${farmId}/readings/latest`)
            .then(adaptReadingResponse)
            .catch((error) => {
                if (error.status === 404) return null
                throw error
            })

export const getFarmHistory = (farmId, limit = 100, offset = 0) =>
    shouldUseMock('history')
        ? mock.getFarmHistory(farmId)
        : httpClient
            .get(`/farms/${farmId}/history?limit=${limit}&offset=${offset}`)
            .then(adaptFarmHistoryResponse)

export const getAllFarms = () =>
    shouldUseMock('farms') ? mock.getAllFarms() : httpClient.get('/farms')

// ── Check-ins / Predictions ───────────────────────────────────────────────────
export const submitCheckin = (farmId, formData) =>
    shouldUseMock('checkin')
        ? mock.submitCheckin(formData).then((prediction) => ({
            ...prediction,
            farm_id: farmId,
        }))
        : (() => {
            console.log('[check-in] request about to send', { farmId, useMock: false })
            return httpClient
                .post(`/farms/${farmId}/checkins`, formData)
                .then((prediction) => adaptPredictionResponse(prediction, farmId))
        })()

export const getPredictionById = (farmId, predictionId) =>
    shouldUseMock('prediction')
        ? mock.getPredictionById(predictionId).then((prediction) => ({
            ...prediction,
            farm_id: farmId,
        }))
        : httpClient
            .get(`/farms/${farmId}/predictions/${predictionId}`)
            .then((prediction) => adaptPredictionResponse(prediction, farmId))

export const getAlerts = (farmId) =>
    shouldUseMock('alerts')
        ? mock.getAlerts(farmId)
        : httpClient.get(`/farms/${farmId}/alerts`).then((alerts) => alerts.map(adaptAlertResponse))

export const acknowledgeAlert = (farmId, alertId) =>
    httpClient.patch(`/farms/${farmId}/alerts/${alertId}`, {})

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
