import { fusedPredictionCopy, getFusedPredictionCopy } from '../content/farmerCopy.js'

const predictionCopyKeys = new Set(Object.keys(fusedPredictionCopy))

// Confidence bands. These are copied from models/fusion/fusion_rules.yaml (bands: strong_min, weak_min).
// Keep them in sync with that file. Below weak_min the model's answer is not used as a verdict.
export const STRONG_MIN = 0.80
export const WEAK_MIN = 0.60

// 'strong' | 'weak' | 'none' for a model confidence between 0 and 1.
export function confidenceBand(confidence) {
  if (!Number.isFinite(confidence)) return 'none'
  if (confidence >= STRONG_MIN) return 'strong'
  if (confidence >= WEAK_MIN) return 'weak'
  return 'none'
}

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

  // A disease name the model is not sure about (below weak_min) must neither confirm a disease nor count as healthy.
  const diseaseIsUnsure = Boolean(diseaseKey) && diseaseKey !== 'healthy'
    && confidenceBand(prediction.disease_conf) === 'none'
  const confidentDiseaseKey = diseaseIsUnsure ? null : diseaseKey

  let fusedPrediction
  let resolvedSeverityLevel = severityLevel

  if (triage === 'out_of_scope') {
    fusedPrediction = 'out_of_scope'
    resolvedSeverityLevel = 'neutral'
  } else if (severity === 'inconclusive') {
    fusedPrediction = 'inconclusive'
    resolvedSeverityLevel = 'neutral'
  } else if (diseaseIsUnsure && severity === 'low') {
    // The only reason this photo looked fine is that the disease model was not sure. That is not "healthy".
    fusedPrediction = 'inconclusive'
    resolvedSeverityLevel = 'neutral'
  } else if (hasNutrientDeficiency && confidentDiseaseKey === 'healthy' && severity === 'low') {
    fusedPrediction = 'nutrient_deficiency'
    resolvedSeverityLevel = 'neutral'
  } else if (severity === 'low') {
    fusedPrediction = 'healthy'
  } else if (confidentDiseaseKey && confidentDiseaseKey !== 'healthy') {
    fusedPrediction = confidentDiseaseKey
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
    disease_band: confidenceBand(prediction.disease_conf),
    // 'uncertain' is for a photo that could not be assessed at all. A disease the model is only unsure about keeps the
    // full result page, where the disease card says "Not sure" and the sensor and nutrient results still show.
    disease_unsure: diseaseIsUnsure,
    status: fusedPrediction === 'out_of_scope'
      ? 'out_of_scope'
      : fusedPrediction === 'inconclusive' && !(diseaseIsUnsure && severity === 'low')
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