import { useFollowUps, useSubmitFollowUpMutation } from '../api/hooks'
import { useFarm } from '../farm/FarmContext'
import Card, { SectionHeader } from './ui/Card'
import { buttonClass } from './ui/styles'

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
    <Card aria-labelledby="follow-up-title">
      <SectionHeader
        id="follow-up-title"
        title="How did it go?"
        description={`On ${when(item.answered_at)} we gave you advice about ${label}. Has the field improved since then?`}
      />
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {OUTCOMES.map(([outcome, text]) => (
          <button
            key={outcome}
            type="button"
            disabled={answer.isPending}
            onClick={() => answer.mutate({ predictionId: item.prediction_id, outcome })}
            className={buttonClass({ variant: 'secondary', block: true })}
          >
            {text}
          </button>
        ))}
      </div>
      {answer.isError && <p role="alert" className="mb-0 mt-3 text-small text-critical-text">Your answer could not be sent. Please try again.</p>}
    </Card>
  )
}
