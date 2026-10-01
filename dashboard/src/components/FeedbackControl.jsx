import React, { useState } from 'react'
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
      <div className="mt-3 px-3 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-sm text-sm flex justify-between items-center">
        <span className="text-[var(--color-text-secondary)]">Feedback recorded.</span>
        <button
          onClick={() => setLocalStatus('idle')}
          className="text-[var(--color-brand)] underline text-sm bg-transparent border-none p-0 cursor-pointer min-h-0 min-w-0 font-normal"
        >
          Edit
        </button>
      </div>
    )
  }

  return (
    <div className="mt-3">
      {localStatus === 'idle' && (
        <div className="flex gap-2">
          <button
            onClick={() => handleConfirm(true)}
            disabled={confirmMutation.isPending}
            className="bg-[var(--color-brand)] text-white px-4 py-2 rounded-sm flex-1 text-sm font-semibold hover:bg-[var(--color-brand-hover)] transition-colors disabled:opacity-60"
          >
            Confirm Correct
          </button>
          <button
            onClick={() => handleConfirm(false)}
            disabled={confirmMutation.isPending}
            className="bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] px-4 py-2 rounded-sm flex-1 text-sm font-semibold hover:bg-[var(--color-neutral-bg)] transition-colors disabled:opacity-60"
          >
            Report Incorrect
          </button>
        </div>
      )}

      {localStatus === 'wrong_selected' && (
        <form onSubmit={handleSubmitWrong} className="flex flex-col gap-2">
          <label className="text-sm text-[var(--color-text-secondary)]">
            Provide details (optional):
          </label>
          <input
            type="text"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Describe the discrepancy"
            className="border border-[var(--color-border)] px-3 py-2 rounded-sm text-sm w-full focus:outline-none focus:border-[var(--color-brand)]"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={confirmMutation.isPending}
              className="bg-[var(--color-brand)] text-white px-4 py-2 rounded-sm flex-1 text-sm font-semibold hover:bg-[var(--color-brand-hover)] transition-colors disabled:opacity-60"
            >
              {confirmMutation.isPending ? 'Submitting…' : 'Submit Feedback'}
            </button>
            <button
              type="button"
              onClick={() => setLocalStatus('idle')}
              className="bg-transparent border-none text-[var(--color-text-secondary)] px-3 py-2 cursor-pointer text-sm rounded-sm hover:text-[var(--color-text-primary)]"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  )
}