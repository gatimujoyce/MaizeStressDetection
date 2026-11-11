import { Link } from 'react-router-dom'
import { useAcknowledgeAlertMutation } from '../api/hooks'
import { ErrorIcon, WarningIcon } from './Icons'
import Badge from './ui/Badge'
import { buttonClass, linkClass } from './ui/styles'

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

function adviceOf(alert) {
  if (!alert.message) return ''
  return alert.message.includes(': ') ? alert.message.split(': ').slice(1).join(': ') : alert.message
}

// An ongoing sensor alert: the one thing on the screen that needs the farmer now.
// Severity is carried by the stripe, the icon and the badge text together.
export default function AttentionAlert({ alert, farmId, meta, titleSuffix = '', showAllLink = false, arrived = false }) {
  const acknowledgeMutation = useAcknowledgeAlertMutation(farmId)
  const critical = alert.severity === 'critical'
  const Icon = critical ? ErrorIcon : WarningIcon

  return (
    <article
      role={arrived ? 'alert' : undefined}
      className={`relative overflow-hidden rounded-card border border-border py-4 pl-6 pr-4 ${critical ? 'bg-critical-bg' : 'bg-warning-bg'} ${arrived ? 'motion-enter' : ''}`}
    >
      <span
        aria-hidden="true"
        className={`absolute inset-y-0 left-0 w-1.5 ${critical ? 'bg-critical-text' : 'bg-warning-text'}`}
      />
      <div className={`flex flex-wrap items-center gap-x-2 gap-y-2 ${critical ? 'text-critical-text' : 'text-warning-text'}`}>
        <span aria-hidden="true" className="flex">
          <Icon size={18} />
        </span>
        <h3 className="m-0 text-heading">
          {STRESS_TITLES[alert.stress_class] || 'Field alert'}{titleSuffix}
        </h3>
        <span className="ml-auto">
          <Badge tone={critical ? 'critical' : 'warning'} icon={false}>{critical ? 'Urgent' : 'Act soon'}</Badge>
        </span>
      </div>
      <p className="mb-0 mt-2 text-body text-ink">{adviceOf(alert)}</p>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        {meta && <span className="text-small text-ink-secondary">{meta}</span>}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          {showAllLink && (
            <Link to="/alerts" className={`inline-flex min-h-11 items-center text-small ${linkClass}`}>
              See all alerts →
            </Link>
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
        </div>
      </div>
      {acknowledgeMutation.isError && (
        <p role="alert" className="mb-0 mt-2 text-small text-critical-text">
          Could not acknowledge this alert. Please try again.
        </p>
      )}
    </article>
  )
}
