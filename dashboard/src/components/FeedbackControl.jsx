import { useState } from 'react'
import { useConfirmPredictionMutation } from '../api/hooks'
import { useAuth } from '../auth/AuthContext'

export default function FeedbackControl({ alertId }) {
  const [localStatus, setLocalStatus] = useState('idle')
  const [comment, setComment] = useState('')
  const { userId } = useAuth()
  const confirmMutation = useConfirmPredictionMutation()

  const handleConfirm = async (isCorrect) => {
    if (isCorrect) {
      await confirmMutation.mutateAsync({ alertId, farmerId: userId || 'farmer-1', confirmed: true, comment: '' })
      setLocalStatus('submitted')
    } else {
      setLocalStatus('wrong_selected')
    }
  }

  const handleSubmitWrong = async (e) => {
    e.preventDefault()
    await confirmMutation.mutateAsync({ alertId, farmerId: userId || 'farmer-1', confirmed: false, comment })
    setLocalStatus('submitted')
  }

  if (localStatus === 'submitted') {
    return (
      <div className="mt-3 flex items-center justify-between rounded-control border border-border bg-surface px-3 py-2 text-small">
        <span className="text-ink-secondary">Feedback recorded.</span>
        <button
          onClick={() => setLocalStatus('idle')}
          className="min-h-12 rounded-control border-2 border-brand bg-surface px-4 py-2 text-small font-bold text-brand underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
        >
          Edit
        </button>
      </div>
    )
  }

  return (
    <div className="mt-3">
      {localStatus === 'idle' && (
        <>
          <p className="mb-3 text-body font-bold text-ink">Does this match what you see?</p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              onClick={() => handleConfirm(true)}
              disabled={confirmMutation.isPending}
              className="min-h-12 flex-1 rounded-control border-2 border-brand bg-surface px-4 py-2 text-small font-bold text-brand hover:bg-brand-tint focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:opacity-60"
            >
              Yes, it matches
            </button>
            <button
              onClick={() => handleConfirm(false)}
              disabled={confirmMutation.isPending}
              className="min-h-12 flex-1 rounded-control border-2 border-brand bg-surface px-4 py-2 text-small font-bold text-brand hover:bg-brand-tint focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:opacity-60"
            >
              No, it is different
            </button>
          </div>
        </>
      )}

      {localStatus === 'wrong_selected' && (
        <form onSubmit={handleSubmitWrong} className="flex flex-col gap-2">
          <label className="text-small text-ink-secondary">
            Provide details (optional):
          </label>
          <input
            type="text"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Describe the discrepancy"
            className="w-full rounded-control border border-control px-3 py-2 text-small text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={confirmMutation.isPending}
              className="min-h-12 flex-1 rounded-control border-2 border-brand bg-surface px-4 py-2 text-small font-bold text-brand hover:bg-brand-tint focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:opacity-60"
            >
              {confirmMutation.isPending ? 'Submitting…' : 'Submit Feedback'}
            </button>
            <button
              type="button"
              onClick={() => setLocalStatus('idle')}
              className="min-h-12 rounded-control border-2 border-brand bg-surface px-4 py-2 text-small font-bold text-brand hover:bg-brand-tint focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  )
}