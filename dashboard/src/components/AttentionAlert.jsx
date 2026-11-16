import { Link } from 'react-router-dom'
import { useAcknowledgeAlertMutation } from '../api/hooks'
import { adviceOf, stressTitle } from '../content/alertTitles'
import { ErrorIcon, WarningIcon } from './Icons'
import AlertRow from './ui/AlertRow'
import Badge from './ui/Badge'
import { buttonClass, linkClass } from './ui/styles'

// An ongoing sensor alert: the one thing on the screen that needs the farmer now.
// Severity is carried by the stripe, the icon and the badge text together.
export default function AttentionAlert({ alert, farmId, meta, titleSuffix = '', showAllLink = false, arrived = false, as = 'li' }) {
  const acknowledgeMutation = useAcknowledgeAlertMutation(farmId)
  const critical = alert.severity === 'critical'
  const Icon = critical ? ErrorIcon : WarningIcon
  return (
    <AlertRow
      as={as}
      tone={critical ? 'critical' : 'warning'}
      tinted
      role={arrived ? 'alert' : undefined}
      className={arrived ? 'motion-enter' : ''}
    >
      <div className={`flex flex-wrap items-center gap-x-2 gap-y-2 ${critical ? 'text-critical-text' : 'text-warning-text'}`}>
        <span aria-hidden="true" className="flex">
          <Icon size={18} />
        </span>
        <h3 className="m-0 text-body font-bold">
          {stressTitle(alert.stress_class)}{titleSuffix}
        </h3>
        <span className="ml-auto">
          <Badge tone={critical ? 'critical' : 'warning'} icon={false}>{critical ? 'Urgent' : 'Act soon'}</Badge>
        </span>
      </div>
      <p className="mb-0 mt-2 text-body text-ink">{adviceOf(alert.message)}</p>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        {meta && <span className="text-small text-ink-secondary">{meta}</span>}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          {showAllLink && (
            <Link to="/alerts" className={`inline-flex min-h-11 items-center text-small ${linkClass}`}>
              See all alerts
            </Link>
          )}
          {farmId && alert.status !== 'acknowledged' && (
            <button
              type="button"
              onClick={() => acknowledgeMutation.mutate(alert.alert_id)}
              disabled={acknowledgeMutation.isPending}
              className={buttonClass({ variant: 'secondary', size: 'sm' })}
            >
              {acknowledgeMutation.isPending ? 'Marking as read…' : 'Mark as read'}
            </button>
          )}
        </div>
      </div>
      {acknowledgeMutation.isError && (
        <p role="alert" className="mb-0 mt-2 text-small text-critical-text">
          Could not mark this alert as read. Please try again.
        </p>
      )}
    </AlertRow>
  )
}
