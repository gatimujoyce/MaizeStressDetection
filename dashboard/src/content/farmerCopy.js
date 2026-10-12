export function humanizeLabel(value) {
  if (typeof value !== 'string' || value.length === 0) return 'Unknown'
  const label = value.replaceAll('_', ' ')
  return `${label[0].toUpperCase()}${label.slice(1)}`
}

export const fusedPredictionCopy = {
  healthy: {
    headline: 'Your maize looks healthy',
    support: 'No stress found in your latest check.',
    action: 'Check again in a week.',
    chipLabel: 'Healthy',
  },
  drought_stress: {
    headline: 'Your maize needs water',
    support: 'Your latest check shows signs of drought stress.',
    action: 'Water the field today, early in the morning or late in the evening.',
    chipLabel: 'Drought stress',
  },
  heat_stress: {
    headline: 'Your maize is under heat stress',
    support: 'Temperatures have been high for your crop.',
    action: 'If you can water, do it early in the morning or late in the evening, and check again tomorrow.',
    chipLabel: 'Heat stress',
  },
  waterlogging_risk: {
    headline: 'Your maize has too much water',
    support: 'The soil has been very wet over several readings.',
    action: 'Check that water can drain from the field, and hold off watering until the soil dries.',
    chipLabel: 'Too much water',
  },
  leaf_blight: {
    headline: 'Your maize shows signs of leaf blight',
    support: 'Your latest photo shows leaf spots that match blight.',
    action: 'Check nearby plants today and ask your extension officer what to do.',
    chipLabel: 'Leaf blight',
  },
  northern_leaf_blight: {
    headline: 'Your maize shows signs of leaf blight',
    support: 'Your latest photo shows leaf spots that match northern leaf blight.',
    action: 'Check nearby plants today and ask your extension officer what to do.',
    chipLabel: 'Northern leaf blight',
  },
  common_rust: {
    headline: 'Your maize shows signs of common rust',
    support: 'Your latest photo shows small reddish-brown bumps on the leaves.',
    action: 'Check nearby plants today. If many leaves are affected, ask your extension officer about treatment.',
    chipLabel: 'Common rust',
  },
  gray_leaf_spot: {
    headline: 'Your maize shows signs of gray leaf spot',
    support: 'Your latest photo shows long, narrow gray or tan spots on the leaves.',
    action: 'Check nearby plants today and ask your extension officer what to do. Warm, humid weather helps it spread.',
    chipLabel: 'Gray leaf spot',
  },
}

export const nutrientStatusLabels = {
  nitrogen_deficiency: 'Low nitrogen',
  phosphorus_deficiency: 'Low phosphorus',
  potassium_deficiency: 'Low potassium',
  zinc_deficiency: 'Low zinc',
}

export const alertCopy = {
  uncertain: {
    title: 'The photo was unclear',
    advice: 'Retake the photo in daylight with one leaf held flat.',
  },
  out_of_scope: {
    title: 'We do not recognise this',
    advice: 'Show a leaf to your extension officer.',
  },
}

export function getFusedPredictionCopy(value) {
  return fusedPredictionCopy[value] ?? {
    headline: 'Your maize needs a closer look',
    support: 'Your latest check found a problem we want you to confirm.',
    action: 'Check the field and retake the photo in daylight.',
    chipLabel: humanizeLabel(value),
  }
}

export function getNutrientStatusLabel(value) {
  if (!value || ['no_deficiency', 'none', 'normal', 'healthy'].includes(value)) {
    return 'Nutrients look fine'
  }
  return nutrientStatusLabels[value] ?? humanizeLabel(value)
}
