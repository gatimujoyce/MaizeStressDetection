import { useState } from 'react'
import { useSubmitFeedbackMutation } from '../api/hooks'

const MATCHED = [['yes', 'Yes, it matches'], ['partly', 'Partly'], ['no', 'No, it is different']]
const ACTIONS = [['followed', 'Yes, I followed the advice'], ['other', 'I did something else'], ['none', 'Not yet']]
const FOUND = [
  ['healthy', 'The plant looks healthy'],
  ['northern_leaf_blight', 'Northern leaf blight'],
  ['gray_leaf_spot', 'Gray leaf spot'],
  ['common_rust', 'Common rust'],
  ['nitrogen_deficiency', 'Not enough nitrogen'],
  ['phosphorus_deficiency', 'Not enough phosphorus'],
  ['potassium_deficiency', 'Not enough potassium'],
  ['something_else', 'Something else'],
  ['not_sure', 'I am not sure'],
]

const choiceClass = (selected) =>
  `min-h-12 flex-1 rounded-control border-2 border-brand px-4 py-2 text-small font-bold focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:opacity-60 ${selected ? 'bg-brand text-white' : 'bg-surface text-brand hover:bg-brand-tint'}`

function Choice({ id, legend, options, value, onChange, disabled }) {
  return (
    <div role="group" aria-labelledby={id} className="flex flex-col gap-2">
      <p id={id} className="m-0 text-body font-bold text-ink">{legend}</p>
      <div className="flex flex-col gap-2 sm:flex-row">
        {options.map(([key, label]) => (
          <button key={key} type="button" aria-pressed={value === key} disabled={disabled} onClick={() => onChange(key)} className={choiceClass(value === key)}>
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}

// A short questionnaire about one result. Sending it again replaces the earlier answers.
export default function FeedbackControl({ predictionId, alertId }) {
  const id = predictionId ?? alertId
  const [answers, setAnswers] = useState({ matched: '', action: '', found: '', comment: '' })
  const [done, setDone] = useState(false)
  const submit = useSubmitFeedbackMutation()
  const set = (key) => (value) => setAnswers((prev) => ({ ...prev, [key]: value }))
  const ready = answers.matched && answers.action

  async function handleSubmit(event) {
    event.preventDefault()
    if (!ready) return
    try {
      await submit.mutateAsync({
        predictionId: id,
        matched: answers.matched,
        actionTaken: answers.action,
        correctLabel: answers.matched === 'yes' ? null : answers.found || null,
        comment: answers.comment.trim() || null,
      })
      setDone(true)
    } catch { /* the error is shown below */ }
  }

  if (done) {
    return (
      <div role="status" className="mt-3 flex items-center justify-between gap-3 rounded-control border border-border bg-surface px-3 py-2 text-small">
        <span className="text-ink-secondary">Thank you. We will ask how it went in about a week.</span>
        <button
          type="button"
          onClick={() => setDone(false)}
          className="min-h-12 rounded-control border-2 border-brand bg-surface px-4 py-2 text-small font-bold text-brand underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
        >
          Change my answers
        </button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="mt-3 flex flex-col gap-4">
      <Choice id={`fb-matched-${id}`} legend="Does this match what you see in the field?" options={MATCHED} value={answers.matched} onChange={set('matched')} disabled={submit.isPending} />
      <Choice id={`fb-action-${id}`} legend="Have you done anything because of this advice?" options={ACTIONS} value={answers.action} onChange={set('action')} disabled={submit.isPending} />
      {(answers.matched === 'partly' || answers.matched === 'no') && (
        <label className="flex flex-col gap-1 text-body font-bold text-ink">
          What do you think it is?
          <select
            value={answers.found}
            onChange={(event) => set('found')(event.target.value)}
            className="min-h-12 rounded-control border-[1.5px] border-control bg-surface px-3 text-small font-normal text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
          >
            <option value="">Choose one (optional)</option>
            {FOUND.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select>
        </label>
      )}
      <label className="flex flex-col gap-1 text-body font-bold text-ink">
        Anything else we should know? (optional)
        <textarea
          rows={2}
          maxLength={500}
          value={answers.comment}
          onChange={(event) => set('comment')(event.target.value)}
          className="rounded-control border-[1.5px] border-control bg-surface px-3 py-2 text-small font-normal text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
        />
      </label>
      {submit.isError && <p role="alert" className="m-0 text-small text-critical-text">{submit.error?.message || 'Your answers could not be sent. Please try again.'}</p>}
      <button
        type="submit"
        disabled={!ready || submit.isPending}
        className="min-h-12 rounded-control border-2 border-brand bg-brand px-4 py-2 text-small font-bold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:opacity-60"
      >
        {submit.isPending ? 'Sending…' : 'Send my answers'}
      </button>
    </form>
  )
}
