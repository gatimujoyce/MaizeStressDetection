// What each trend chart shows: its title, unit and how a day-to-day change is worded.
// Kept apart from ReadingTrendCard so that file only exports a component.
export const FIELDS = {
    soil_moisture: { title: 'Soil moisture', unit: '%', decimals: 0, tolerance: 1.5 },
    temperature: { title: 'Temperature', unit: ' °C', decimals: 1, tolerance: 0.5 },
    humidity: { title: 'Humidity', unit: '%', decimals: 0, tolerance: 2 },
    // The sensor's value is the dew point gap (air temperature minus dew point): SMALL means damp air and wet leaves, so the
    // card says so in words instead of showing a score that rises as the leaves dry.
    leaf_wetness: {
        title: 'Leaf dampness', unit: ' °C', decimals: 1, tolerance: 0.5,
        note: 'This is the gap between air temperature and dew point. A small gap means damp air and wet leaves; below 3 °C the leaves are likely wet. The 3 °C line is provisional.',
        wording: { up: 'Drier than the day before', down: 'Damper than the day before' },
    },
    nitrogen_mg_kg: { title: 'Nitrogen', unit: ' mg/kg', decimals: 0, tolerance: 2, alertClass: 'low_nitrogen' },
    phosphorus_mg_kg: { title: 'Phosphorus', unit: ' mg/kg', decimals: 0, tolerance: 1, alertClass: 'low_phosphorus' },
    potassium_mg_kg: { title: 'Potassium', unit: ' mg/kg', decimals: 0, tolerance: 5, alertClass: 'low_potassium' },
}

export const formatNumber = (value, decimals) => Number(value).toFixed(decimals).replace(/\.0+$/, '')

export const FIELD_ORDER = ['soil_moisture', 'temperature', 'humidity', 'leaf_wetness']
export const NPK_FIELD_ORDER = ['nitrogen_mg_kg', 'phosphorus_mg_kg', 'potassium_mg_kg']

export function describeChange(change, field) {
    const { tolerance, decimals, unit, wording } = FIELDS[field]
    if (change === null || change === undefined) return null
    if (Math.abs(change) < tolerance) return { arrow: '→', text: 'About the same as the day before' }
    const size = `${formatNumber(Math.abs(change), decimals)}${unit.trim() === '%' ? ' points' : unit}`
    return change > 0
        ? { arrow: '↑', text: wording ? wording.up : `${size} higher than the day before` }
        : { arrow: '↓', text: wording ? wording.down : `${size} lower than the day before` }
}
