// Single data-access layer.
// Feature flag: VITE_USE_MOCK_API=true → calls mockApi.js
//               VITE_USE_MOCK_API=false → calls real backend via httpClient.js
import * as mock from './mockApi'
import { httpClient } from './httpClient'

const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true'

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (credentials) =>
    USE_MOCK ? mock.login(credentials) : httpClient.post('/auth/login', credentials)

export const register = (data) =>
    USE_MOCK ? mock.register(data) : httpClient.post('/auth/register', data)

// ── Farms ─────────────────────────────────────────────────────────────────────
export const getFarmerFarm = (farmerId) =>
    USE_MOCK ? mock.getFarmerFarm(farmerId) : httpClient.get(`/farms/farmer/${farmerId}`)

export const createFarm = (data) =>
    USE_MOCK ? mock.createFarm(data) : httpClient.post('/farms', data)

export const getFarmStatus = (farmId) =>
    USE_MOCK ? mock.getFarmStatus(farmId) : httpClient.get(`/farms/${farmId}/status`)

export const getFarmHistory = (farmId, days = 30) =>
    USE_MOCK ? mock.getFarmHistory(farmId, days) : httpClient.get(`/farms/${farmId}/history?days=${days}`)

export const getAllFarms = () =>
    USE_MOCK ? mock.getAllFarms() : httpClient.get('/farms')

// ── Check-ins / Predictions ───────────────────────────────────────────────────
export const submitCheckin = (formData) =>
    USE_MOCK ? mock.submitCheckin(formData) : httpClient.post('/checkins', formData)

export const getPredictionById = (predictionId) =>
    USE_MOCK ? mock.getPredictionById(predictionId) : httpClient.get(`/predictions/${predictionId}`)

export const getAlerts = (farmId) =>
    USE_MOCK ? mock.getAlerts(farmId) : httpClient.get(`/farms/${farmId}/alerts`)

export const getAllAlerts = () =>
    USE_MOCK ? mock.getAllAlerts() : httpClient.get('/alerts')

// ── Feedback ──────────────────────────────────────────────────────────────────
export const confirmPrediction = (alertId, farmerId, confirmed, comment = '') =>
    USE_MOCK
        ? mock.confirmPrediction(alertId, farmerId, confirmed, comment)
        : httpClient.post('/feedback', { prediction_id: alertId, farmer_id: farmerId, farmer_confirmed: confirmed, comment })

export const getFeedbackList = (filterNotAccurate = false) =>
    USE_MOCK ? mock.getFeedbackList(filterNotAccurate) : httpClient.get(`/feedback${filterNotAccurate ? '?not_accurate=true' : ''}`)

// ── Admin / System ────────────────────────────────────────────────────────────
export const getSystemHealth = () =>
    USE_MOCK ? mock.getSystemHealth() : httpClient.get('/system/health')

export const getAllUsers = () =>
    USE_MOCK ? mock.getAllUsers() : httpClient.get('/users')

export const getModelVersions = () =>
    USE_MOCK ? mock.getModelVersions() : httpClient.get('/models')

export const switchModelVersion = (modelType, versionId) =>
    USE_MOCK
        ? mock.switchModelVersion(modelType, versionId)
        : httpClient.patch(`/models/${modelType}/activate`, { version_id: versionId })

export const triggerRetrain = (modelType) =>
    USE_MOCK ? mock.triggerRetrain(modelType) : httpClient.post('/retrain', { model_type: modelType })

export const getRetrainingJobs = () =>
    USE_MOCK ? mock.getRetrainingJobs() : httpClient.get('/retrain/jobs')

export const getSmsLog = () =>
    USE_MOCK ? mock.getSmsLog() : httpClient.get('/sms/log')
