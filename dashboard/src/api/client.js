// Single data-access layer.
// Feature flag: VITE_USE_MOCK_API=true → calls mockApi.js
//               VITE_USE_MOCK_API=false → calls real backend via httpClient.js
import * as mock from './mockApi'
import { httpClient } from './httpClient'
import { describeNutrient, describeResult } from './resultWording'
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
        severity_label: normalizedSeverity === 'high' ? 'Urgent' : normalizedSeverity === 'medium' ? 'Act soon' : 'Note',
    }
}

function adaptReadingResponse(reading) {
    // A box with a dead sensor sends the other values only, so one working value is enough.
    const tileFields = ['soil_moisture', 'temperature', 'humidity']
    const hasValidTileValues = tileFields.some((field) =>
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
            at: Date.parse(prediction.created_at),
            result: describeResult(prediction),
            disease: describeResult(prediction),
            nutrient: describeNutrient(prediction),
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
    hasNpkSensor: Boolean(farm.has_npk_sensor),
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
        has_npk_sensor: Boolean(data.hasNpkSensor),
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

// 404: the farm has no readings yet. 503: the real models are not configured.
export const getLatestReadingClassification = (farmId) =>
    httpClient.get(`/farms/${farmId}/readings/latest/classification`)
        .catch((error) => {
            if (error.status === 404 || error.status === 503) return null
            throw error
        })

export const getReadingTrend = (farmId, range = '7d') =>
    httpClient.get(`/farms/${farmId}/readings/trend?range=${range}`)

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
// Feedback always goes to the real server (it needs a real result to attach to).
export const submitFeedback = ({ predictionId, matched, actionTaken, correctLabel, comment }) =>
    httpClient.post(`/predictions/${predictionId}/feedback`, {
        matched,
        action_taken: actionTaken,
        correct_label: correctLabel,
        comment,
    })

export const getFollowUps = (farmId) => httpClient.get(`/farms/${farmId}/follow-ups`)

export const submitFollowUp = ({ predictionId, outcome }) =>
    httpClient.post(`/predictions/${predictionId}/follow-up`, { outcome })

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

// Admin endpoints always use the authenticated backend. Keep these separate
// from farmer queries and legacy mock helpers so the admin UI cannot silently
// render demo data when backend integration is enabled.
export const getAdminFarms = (includeDeleted = false) =>
    httpClient.get(`/admin/farms${includeDeleted ? '?include_deleted=true' : ''}`)

export const getAdminUsers = () =>
    httpClient.get('/admin/users')

export const createAdminUser = (data) =>
    httpClient.post('/admin/users', data)

export const getAdminFeedback = () =>
    httpClient.get('/admin/feedback')

export const getAdminModelVersions = () =>
    httpClient.get('/admin/model-versions')

export const setAdminModelVersionActive = (versionId, isActive) =>
    httpClient.patch(`/admin/model-versions/${versionId}`, { is_active: isActive })

export const getAdminRetrainingJobs = () =>
    httpClient.get('/admin/retraining-jobs')

export const requestAdminRetrain = (modelName) =>
    httpClient.post('/admin/retrain', { model_name: modelName })

export const getAdminSmsLog = () =>
    httpClient.get('/admin/sms-log')

export const getGrowthStage = (farmId) => httpClient.get(`/farms/${farmId}/growth-stage`)

export const requestSensor = (farmId, note) =>
    httpClient.post(`/farms/${farmId}/sensor-request`, { note: note || null }).then(mapFarmResponse)

export const cancelSensorRequest = (farmId) =>
    httpClient.delete(`/farms/${farmId}/sensor-request`).then(mapFarmResponse)

export const getAdminSensorRequests = () =>
    httpClient.get('/admin/sensor-requests')

export const markAdminSensorInstalled = (farmId, hasNpkSensor) =>
    httpClient.post(`/admin/farms/${farmId}/sensor-installed`, hasNpkSensor === undefined ? {} : { has_npk_sensor: hasNpkSensor })

export const cancelAdminSensorRequest = (farmId) =>
    httpClient.post(`/admin/farms/${farmId}/sensor-request/cancel`)

export const markAdminSensorContacted = (farmId) =>
    httpClient.post(`/admin/farms/${farmId}/sensor-request/contact`)
