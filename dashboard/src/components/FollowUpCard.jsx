import { useFollowUps, useSubmitFollowUpMutation } from '../api/hooks'
import { useFarm } from '../farm/FarmContext'

const OUTCOMES = [['better', 'It got better'], ['same', 'No change'], ['worse', 'It got worse'], ['not_acted', 'I did not act on it']]

const when = (value) => new Date(value).toLocaleDateString('en-KE', { day: 'numeric', month: 'long' })

// About a week after a farmer answered the questions: "How did it go?". Shows one result at a time.
export default function FollowUpCard() {
  const { selectedFarmId } = useFarm()
  const { data: due = [] } = useFollowUps(selectedFarmId)
  const answer = useSubmitFollowUpMutation(selectedFarmId)
  const item = due[0]
  if (!item) return null
  const label = item.label && item.label !== 'healthy' ? item.label.replaceAll('_', ' ') : 'your maize'

  return (
    <section aria-labelledby="follow-up-title" className="mb-4 rounded-card border border-border bg-surface p-4">
      <h2 id="follow-up-title" className="m-0 text-heading text-ink">How did it go?</h2>
      <p className="mb-3 mt-1 text-body text-ink">
        On {when(item.answered_at)} we gave you advice about {label}. Has the field improved since then?
      </p>
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
        {OUTCOMES.map(([outcome, text]) => (
          <button
            key={outcome}
            type="button"
            disabled={answer.isPending}
            onClick={() => answer.mutate({ predictionId: item.prediction_id, outcome })}
            className="min-h-12 flex-1 rounded-control border-2 border-brand bg-surface px-4 py-2 text-small font-bold text-brand hover:bg-brand-tint focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:opacity-60"
          >
            {text}
          </button>
        ))}
      </div>
      {answer.isError && <p role="alert" className="mb-0 mt-2 text-small text-critical-text">Your answer could not be sent. Please try again.</p>}
    </section>
  )
}
