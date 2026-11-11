import Badge from './ui/Badge'
import { cardClass, buttonClass } from './ui/styles'
import FeedbackControl from './FeedbackControl'
import { useAcknowledgeAlertMutation } from '../api/hooks'

const STRESS_TITLES = {
  heat_stress: 'Heat stress',
  drought_stress: 'Drought stress',
  waterlogging_risk: 'Waterlogging risk',
  low_nitrogen: 'Low nitrogen',
  low_phosphorus: 'Low phosphorus',
  low_potassium: 'Low potassium',
  sensor_silent: 'Sensor not reporting',
  npk_silent: 'NPK sensor not reporting',
}

export default function AlertCard({ alert, farmId, arrived = false }) {
  const acknowledgeMutation = useAcknowledgeAlertMutation(farmId)
  const severity = alert.severity
  const isSensor = alert.source === 'sensor'
  const label = isSensor
    ? `${STRESS_TITLES[alert.stress_class] || 'Field alert'} · ${alert.severity_label}`
    : `Photo check-in · ${alert.severity_label}`

  return (
    <article className={`flex flex-col items-start gap-3 ${cardClass} ${arrived ? 'motion-enter' : ''}`}>
      <Badge tone={severity}>{label}</Badge>
      {alert.message && (
        <p className="m-0 text-body text-ink">
          {alert.message.includes(': ') ? alert.message.split(': ').slice(1).join(': ') : alert.message}
        </p>
      )}
      {alert.prediction_id && (
        <div className="w-full">
          <FeedbackControl predictionId={alert.prediction_id} />
        </div>
      )}
      {farmId && alert.status !== 'acknowledged' && (
        <button
          type="button"
          onClick={() => acknowledgeMutation.mutate(alert.alert_id)}
          disabled={acknowledgeMutation.isPending}
          className={buttonClass({ variant: 'secondary', size: 'sm' })}
        >
          {acknowledgeMutation.isPending ? 'Acknowledging…' : 'Mark as read'}
        </button>
      )}
      {acknowledgeMutation.isError && (
        <p role="alert" className="m-0 text-small text-critical-text">
          Could not acknowledge this alert. Please try again.
        </p>
      )}
    </article>
  )
}