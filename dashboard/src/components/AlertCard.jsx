import { alertCopy } from '../content/farmerCopy'
import StatusChip from './StatusChip'
import FeedbackControl from './FeedbackControl'

export default function AlertCard({ alert }) {
  const isInformation = alert.status === 'uncertain' || alert.status === 'out_of_scope'
  const severity = isInformation
    ? 'neutral'
    : alert.severity === 'critical'
      ? 'critical'
      : 'warning'
  const label = isInformation
    ? 'For your information'
    : severity === 'critical'
      ? 'Urgent'
      : 'Warning'
  const copy = isInformation ? alertCopy[alert.status] : null
  const title = copy?.title ?? alert.plain_summary
  const advice = copy?.advice ?? alert.message

  return (
    <article className="flex flex-col items-start gap-3 rounded-2xl border border-border bg-surface p-4">
      <StatusChip status={severity} label={label} />
      <h3 className="m-0 w-full text-[17px] font-bold text-ink">{title}</h3>
      <p className="w-full text-[17px] text-ink">{advice}</p>
      {!isInformation && (
        <div className="w-full">
          <FeedbackControl alertId={alert.alert_id} />
        </div>
      )}
    </article>
  )
}
