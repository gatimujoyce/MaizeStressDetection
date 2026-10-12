// Mirrors backend app/services/sensor.py. Replace with values from the API when the backend exposes them.

export const SOIL_PROFILES = {
  sandy_loam: { label: 'sandy loam', fieldCapacity: 20, wiltingPoint: 7.5, saturation: 30 },
  loam: { label: 'loam', fieldCapacity: 40, wiltingPoint: 12.5, saturation: 45 },
  silt_loam: { label: 'silt loam', fieldCapacity: 42, wiltingPoint: 14, saturation: 48 },
  clay: { label: 'clay', fieldCapacity: 50, wiltingPoint: 17.5, saturation: 58 },
}

const STRESS_READINGS = {
  normal: { pctFC: 80, temperature: 23.5, humidity: 55 },
  drought_stress: { pctFC: 35, temperature: 27, humidity: 30 },
  heat_stress: { pctFC: 75, temperature: 36, humidity: 45 },
  waterlogging_risk: { pctFC: 125, temperature: 22, humidity: 85 },
}

const roundToTwo = (value) => Math.round(value * 100) / 100

export function moistureScale(soilType) {
  const { fieldCapacity, wiltingPoint, saturation } = SOIL_PROFILES[soilType] ?? SOIL_PROFILES.loam
  const droughtLimit = 0.55 * fieldCapacity
  const wetLimit = 1.1 * fieldCapacity
  return {
    min: wiltingPoint,
    max: saturation,
    zones: [
      { from: wiltingPoint, to: droughtLimit, label: 'Too dry', tone: 'warning' },
      { from: droughtLimit, to: fieldCapacity, label: 'Good', tone: 'healthy' },
      { from: fieldCapacity, to: wetLimit, label: 'Getting wet', tone: 'neutral' },
      { from: wetLimit, to: saturation, label: 'Too wet', tone: 'warning' },
    ],
    goodRange: [Math.round(droughtLimit), Math.round(fieldCapacity)],
  }
}

export function temperatureScale() {
  return {
    min: 10,
    max: 45,
    zones: [
      { from: 10, to: 18, label: 'Cool', tone: 'neutral' },
      { from: 18, to: 29, label: 'Comfortable', tone: 'healthy' },
      { from: 29, to: 32, label: 'Warm', tone: 'neutral' },
      { from: 32, to: 45, label: 'Hot', tone: 'warning' },
    ],
  }
}

export function humidityScale() {
  return {
    min: 0,
    max: 100,
    zones: [
      { from: 0, to: 30, label: 'Dry air', tone: 'neutral' },
      { from: 30, to: 80, label: 'Usual', tone: 'neutral' },
      { from: 80, to: 100, label: 'Humid', tone: 'neutral' },
    ],
  }
}

export function zoneFor(scale, value) {
  const clamped = Math.max(scale.min, Math.min(scale.max, value))
  return scale.zones.find((zone, index) =>
    clamped <= zone.to || index === scale.zones.length - 1
  )
}

export function dewPointDepression(tempC, rhPercent) {
  const a = 17.27
  const b = 237.7
  const rh = Math.max(1, Math.min(100, rhPercent))
  const alpha = (a * tempC) / (b + tempC) + Math.log(rh / 100)
  const dewPoint = (b * alpha) / (a - alpha)
  return roundToTwo(tempC - dewPoint)
}

export function mockReading(soilType, stressClass) {
  const soil = SOIL_PROFILES[soilType] ?? SOIL_PROFILES.loam
  const stress = STRESS_READINGS[stressClass] ?? STRESS_READINGS.normal
  const soilMoisture = Math.max(
    soil.wiltingPoint,
    Math.min(soil.saturation, (stress.pctFC / 100) * soil.fieldCapacity),
  )
  const leafWetness = dewPointDepression(stress.temperature, stress.humidity)
  return {
    soil_moisture: roundToTwo(soilMoisture),
    temperature: roundToTwo(stress.temperature),
    humidity: roundToTwo(stress.humidity),
    leaf_wetness: roundToTwo(leafWetness),
  }
}
