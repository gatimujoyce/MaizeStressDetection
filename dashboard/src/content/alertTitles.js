// Names for sensor alert classes, as farmers see them. One list, used by every alert view.
export const STRESS_TITLES = {
  heat_stress: 'Heat stress',
  drought_stress: 'Drought stress',
  waterlogging_risk: 'Waterlogging risk',
  low_nitrogen: 'Low nitrogen',
  low_phosphorus: 'Low phosphorus',
  low_potassium: 'Low potassium',
  sensor_silent: 'Sensor not reporting',
  npk_silent: 'NPK sensor not reporting',
}

export const stressTitle = (stressClass) => STRESS_TITLES[stressClass] || 'Field alert'

// The advice part of an alert message ("Heat stress: Water in the evening..." -> "Water in the evening...").
export function adviceOf(message) {
  if (!message) return ''
  return message.includes(': ') ? message.split(': ').slice(1).join(': ') : message
}
