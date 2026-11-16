import { useId, useState } from 'react'
import { Link } from 'react-router-dom'
import Badge from './ui/Badge'
import AlertRow from './ui/AlertRow'
import { buttonClass, linkClass } from './ui/styles'
import useNow from './ui/useNow'
import FeedbackControl from './FeedbackControl'
import { useAcknowledgeAlertMutation } from '../api/hooks'
import { adviceOf, stressTitle } from '../content/alertTitles'
import { formatWhen } from '../content/dates'

// One recent alert, as a row in the Home screen's alert list. The feedback questions for a photo result stay one
// tap away instead of open on every row, so a few recent alerts do not fill the screen.
export default function AlertCard({ alert, farmId, arrived = false }) {
  const acknowledgeMutation = useAcknowledgeAlertMutation(farmId)
  const [asking, setAsking] = useState(false)
  const questionsId = useId()
  const now = useNow()
  const isSensor = alert.source === 'sensor'
  const label = isSensor
    ? `${stressTitle(alert.stress_class)} · ${alert.severity_label}`
    : `Photo check-in · ${alert.severity_label}`
  const unread = farmId && alert.status !== 'acknowledged'

  return (
    <AlertRow tone={alert.severity} className={`flex flex-col items-start gap-2 ${arrived ? 'motion-enter' : ''}`}>
      <div className="flex w-full flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <Badge tone={alert.severity}>{label}</Badge>
        {alert.created_at && <span className="text-small text-ink-secondary">{formatWhen(alert.created_at, now)}</span>}
      </div>
      {alert.message && <p className="m-0 text-body text-ink">{adviceOf(alert.message)}</p>}
      {(alert.prediction_id || unread) && (
        <div className="flex flex-wrap items-center gap-x-6 gap-y-1">
          {alert.prediction_id && farmId && (
            <Link to={`/result/${farmId}/${alert.prediction_id}`} className={`inline-flex min-h-11 items-center text-small ${linkClass}`}>
              View result
            </Link>
          )}
          {alert.prediction_id && (
            <button
              type="button"
              aria-expanded={asking}
              aria-controls={questionsId}
              onClick={() => setAsking((value) => !value)}
              className={buttonClass({ variant: 'quiet', size: 'sm' })}
            >
              Tell us if this result was right
            </button>
          )}
          {unread && (
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
      )}
      {alert.prediction_id && asking && (
        <div id={questionsId} className="w-full">
          <FeedbackControl predictionId={alert.prediction_id} />
        </div>
      )}
      {acknowledgeMutation.isError && (
        <p role="alert" className="m-0 text-small text-critical-text">
          Could not mark this alert as read. Please try again.
        </p>
      )}
    </AlertRow>
  )
}
