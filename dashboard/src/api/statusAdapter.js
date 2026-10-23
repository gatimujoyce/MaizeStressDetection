import { fusedPredictionCopy, getFusedPredictionCopy } from '../content/farmerCopy.js'

const predictionCopyKeys = new Set(Object.keys(fusedPredictionCopy))

function normalizeLabel(label) {
  if (typeof label !== 'string') return null
  return label
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
}

function toCopyKey(label) {
  const normalized = normalizeLabel(label)
  if (normalized === 'normal') return 'healthy'
  return predictionCopyKeys.has(normalized) ? normalized : null
}

function adaptPrediction(prediction, farmId) {
  const severity = normalizeLabel(prediction.severity)
  const severityLevel = {
    low: 'healthy',
    medium: 'warning',
    high: 'critical',
    inconclusive: 'neutral',
  }[severity] ?? 'neutral'

  const triage = normalizeLabel(prediction.triage_result)
  const diseaseKey = toCopyKey(prediction.disease_label)
  const sensorKey = toCopyKey(prediction.sensor_label)
  const nutrientLabel = normalizeLabel(prediction.nutrient_label)
  const hasNutrientDeficiency = nutrientLabel?.endsWith('_deficiency')
    && nutrientLabel !== 'no_deficiency'

  let fusedPrediction
  let resolvedSeverityLevel = severityLevel

  if (triage === 'out_of_scope') {
    fusedPrediction = 'out_of_scope'
    resolvedSeverityLevel = 'neutral'
  } else if (severity === 'inconclusive') {
    fusedPrediction = 'inconclusive'
    resolvedSeverityLevel = 'neutral'
  } else if (hasNutrientDeficiency && diseaseKey === 'healthy' && severity === 'low') {
    fusedPrediction = 'nutrient_deficiency'
    resolvedSeverityLevel = 'neutral'
  } else if (severity === 'low') {
    fusedPrediction = 'healthy'
  } else if (diseaseKey && diseaseKey !== 'healthy') {
    fusedPrediction = diseaseKey
  } else if (sensorKey) {
    fusedPrediction = sensorKey
  } else {
    fusedPrediction = 'inconclusive'
    resolvedSeverityLevel = 'neutral'
  }

  return {
    ...prediction,
    id: prediction.id,
    prediction_id: prediction.id,
    farm_id: farmId,
    fused_prediction: fusedPrediction,
    severity_level: resolvedSeverityLevel,
    status: fusedPrediction === 'out_of_scope'
      ? 'out_of_scope'
      : fusedPrediction === 'inconclusive'
        ? 'uncertain'
        : 'confirmed',
    created_at: prediction.created_at,
    disease_confidence: prediction.disease_conf,
    nutrient_confidence: prediction.nutrient_conf,
    recommendation: getFusedPredictionCopy(fusedPrediction).action,
    ...(prediction.nutrient_label != null
      ? { nutrient_status: prediction.nutrient_label }
      : {}),
  }
}

export function adaptPredictionResponse(prediction, farmId) {
  return adaptPrediction(prediction, farmId)
}

export function adaptFarmStatus(response) {
  const prediction = response.latest_prediction
  if (!prediction) {
    return {
      farm_id: response.farm_id,
      has_data: false,
    }
  }

  return {
    ...adaptPrediction(prediction, response.farm_id),
    has_data: true,
  }
}
