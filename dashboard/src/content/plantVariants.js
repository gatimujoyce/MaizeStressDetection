const VARIANT_BY_PREDICTION = {
  healthy: 'healthy',
  drought_stress: 'droop',
  heat_stress: 'droop',
  waterlogging_risk: 'wet',
  leaf_blight: 'disease',
  northern_leaf_blight: 'disease',
  common_rust: 'disease',
  gray_leaf_spot: 'disease',
}

export function plantVariantFor(prediction, severity) {
  return VARIANT_BY_PREDICTION[prediction]
    ?? (severity === 'healthy' ? 'healthy' : 'droop')
}
