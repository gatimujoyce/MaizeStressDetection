// How activity-log entries read, shared by the full Activity log and "Your recent actions" on the admin profile.
export const ACTION_LABELS = {
  'user.update': 'Edited farmer',
  'user.create_admin': 'Added administrator',
  'user.password_reset': 'Sent temporary password',
  'farm.create': 'Added farm',
  'farm.update': 'Edited farm',
  'farm.archive': 'Archived farm',
  'farm.restore': 'Restored farm',
  'farm.device_key_created': 'Made sensor box key',
  'farm.device_key_revoked': 'Revoked sensor box key',
}

export const FIELD_LABELS = {
  name: 'Name', phone: 'Phone', location: 'County', soil_type: 'Soil', size_acres: 'Size (acres)', planting_date: 'Planting date',
  water_source: 'Water source', seed_variety: 'Seed variety', has_npk_sensor: 'NPK sensor', device_key: 'Sensor box key',
}

export const actionLabel = (action) => ACTION_LABELS[action] ?? action

export const showValue = (value) => (value === null || value === undefined || value === '' ? 'empty' : value === 'True' ? 'on' : value === 'False' ? 'off' : String(value).replaceAll('_', ' '))
