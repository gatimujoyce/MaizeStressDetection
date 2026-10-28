import StatusChip from './StatusChip'
import FeedbackControl from './FeedbackControl'
import { useAcknowledgeAlertMutation } from '../api/hooks'

const STRESS_TITLES = {
  heat_stress: 'Heat stress',
  drought_stress: 'Drought stress',
  waterlogging_risk: 'Waterlogging risk',
}

export default function AlertCard({ alert, farmId }) {
  const acknowledgeMutation = useAcknowledgeAlertMutation(farmId)
  const severity = alert.severity
  const isSensor = alert.source === 'sensor'
  const label = isSensor
    ? `${STRESS_TITLES[alert.stress_class] || 'Field alert'} · ${alert.severity_label}`
    : alert.severity_label

  return (
    <article className="flex flex-col items-start gap-3 rounded-2xl border border-border bg-surface p-4">
      <StatusChip status={severity} label={label} />
      {isSensor && alert.message && (
        <p className="m-0 text-sm">
          {alert.message.includes(': ') ? alert.message.split(': ').slice(1).join(': ') : alert.message}
        </p>
      )}
      {alert.prediction_id && (
        <div className="w-full">
          <FeedbackControl alertId={alert.alert_id} />
        </div>
      )}
      {farmId && alert.status !== 'acknowledged' && (
        <button
          type="button"
          onClick={() => acknowledgeMutation.mutate(alert.alert_id)}
          disabled={acknowledgeMutation.isPending}
          className="min-h-11 rounded-xl border border-brand px-4 py-2 text-sm font-semibold text-brand disabled:opacity-60"
        >
          {acknowledgeMutation.isPending ? 'Acknowledging…' : 'Mark as read'}
        </button>
      )}
      {acknowledgeMutation.isError && (
        <p role="alert" className="m-0 text-sm text-critical-text">
          Could not acknowledge this alert. Please try again.
        </p>
      )}
    </article>
  )
}