import assert from 'node:assert/strict'
import test from 'node:test'
import { adaptFarmStatus, adaptPredictionResponse } from '../src/api/statusAdapter.js'
import { getFusedPredictionCopy } from '../src/content/farmerCopy.js'

const timestamp = '2026-10-22T10:00:00Z'

const scenarios = [
  ['healthy', 'Low', 'Healthy', 'Normal', 'in_scope', 'No Deficiency', 'healthy'],
  ['common_rust', 'High', 'Common Rust', 'Waterlogging Risk', 'in_scope', 'No Deficiency', 'common_rust'],
  ['northern_leaf_blight', 'High', 'Northern Leaf Blight', 'Waterlogging Risk', 'in_scope', 'No Deficiency', 'northern_leaf_blight'],
  ['gray_leaf_spot', 'High', 'Gray Leaf Spot', 'Heat Stress', 'in_scope', 'No Deficiency', 'gray_leaf_spot'],
  ['drought_stress', 'Medium', 'Healthy', 'Drought Stress', 'in_scope', 'No Deficiency', 'drought_stress'],
  ['heat_stress', 'Medium', 'Healthy', 'Heat Stress', 'in_scope', 'No Deficiency', 'heat_stress'],
  ['waterlogging_risk', 'Medium', 'Healthy', 'Waterlogging Risk', 'in_scope', 'No Deficiency', 'waterlogging_risk'],
  ['nutrient_deficiency', 'Low', 'Healthy', 'Normal', 'in_scope', 'Nitrogen Deficiency', 'nutrient_deficiency'],
  ['out_of_scope', 'Inconclusive', 'Healthy', 'Normal', 'out_of_scope', 'No Deficiency', 'out_of_scope'],
  ['inconclusive', 'Inconclusive', 'Common Rust', 'Normal', 'in_scope', 'No Deficiency', 'inconclusive'],
]

function backendStatus([, severity, disease, sensor, triage, nutrient]) {
  return {
    farm_id: 'farm-123',
    status: severity,
    latest_prediction: {
      severity,
      disease_label: disease,
      disease_conf: 0.9,
      sensor_label: sensor,
      sensor_conf: 0.9,
      nutrient_label: nutrient,
      nutrient_conf: 0.9,
      triage_result: triage,
      created_at: timestamp,
    },
  }
}

test('maps every fixed backend stub scenario to its intended verdict copy', () => {
  for (const scenario of scenarios) {
    const [name, severity, , , , , expectedKey] = scenario
    const result = adaptFarmStatus(backendStatus(scenario))

    assert.equal(result.fused_prediction, expectedKey, name)
    assert.equal(result.has_data, true, name)
    assert.equal(result.created_at, timestamp, name)
    assert.ok(getFusedPredictionCopy(result.fused_prediction).action, name)

    if (name === 'inconclusive' || name === 'out_of_scope') {
      assert.equal(result.severity_level, 'neutral', name)
    } else if (name === 'nutrient_deficiency') {
      assert.equal(result.severity_level, 'neutral', name)
    } else {
      assert.equal(
        result.severity_level,
        { Low: 'healthy', Medium: 'warning', High: 'critical' }[severity],
        name,
      )
    }
  }
})

test('out-of-scope and inconclusive copy never gives disease-specific advice', () => {
  const outOfScope = adaptFarmStatus(backendStatus(scenarios.find(([name]) => name === 'out_of_scope')))
  const inconclusive = adaptFarmStatus(backendStatus(scenarios.find(([name]) => name === 'inconclusive')))

  assert.equal(getFusedPredictionCopy(outOfScope.fused_prediction).action, 'Show a leaf to your extension officer.')
  assert.equal(getFusedPredictionCopy(inconclusive.fused_prediction).action, 'Retake the photo in daylight with one leaf held flat.')
})

test('returns an empty status when there is no prediction', () => {
  assert.deepEqual(adaptFarmStatus({ farm_id: 'farm-123', latest_prediction: null }), {
    farm_id: 'farm-123',
    has_data: false,
  })
})

test('adapts direct predictions with the same safe verdict rules as farm status', () => {
  const prediction = {
    id: 'prediction-123',
    severity: 'Inconclusive',
    disease_label: 'Common Rust',
    disease_conf: 0.9,
    sensor_label: 'Normal',
    sensor_conf: 0.9,
    nutrient_label: 'No Deficiency',
    nutrient_conf: 0.9,
    triage_result: 'out_of_scope',
    created_at: timestamp,
    recommendation: 'Do not expose backend disease advice for this state.',
  }
  const result = adaptPredictionResponse(prediction, 'farm-456')

  assert.equal(result.prediction_id, prediction.id)
  assert.equal(result.farm_id, 'farm-456')
  assert.equal(result.fused_prediction, 'out_of_scope')
  assert.equal(result.status, 'out_of_scope')
  assert.equal(result.severity_level, 'neutral')
  assert.equal(result.recommendation, getFusedPredictionCopy('out_of_scope').action)
  assert.equal(result.sensor_conditions, undefined)
})

test('does not expose disease advice for direct inconclusive predictions', () => {
  const result = adaptPredictionResponse({
    id: 'prediction-789',
    severity: 'Inconclusive',
    disease_label: 'Common Rust',
    disease_conf: 0.9,
    sensor_label: 'Normal',
    sensor_conf: 0.9,
    triage_result: 'in_scope',
    created_at: timestamp,
    recommendation: 'Backend disease treatment advice.',
  }, 'farm-456')

  assert.equal(result.fused_prediction, 'inconclusive')
  assert.equal(result.status, 'uncertain')
  assert.equal(result.severity_level, 'neutral')
  assert.equal(result.recommendation, getFusedPredictionCopy('inconclusive').action)
})

test('uses neutral generic copy for unknown non-healthy labels rather than disease advice', () => {
  const result = adaptFarmStatus({
    farm_id: 'farm-123',
    latest_prediction: {
      severity: 'High',
      disease_label: 'Unmapped Finding',
      sensor_label: 'Unmapped Sensor State',
      triage_result: 'in_scope',
      created_at: timestamp,
    },
  })

  assert.equal(result.fused_prediction, 'inconclusive')
  assert.equal(result.severity_level, 'neutral')
})
