import React, { useState } from 'react'
import { confirmPrediction } from '../api/mockApi'

export default function FeedbackControl({ alertId }) {
  const [status, setStatus] = useState('idle')
  const [comment, setComment] = useState('')

  const handleConfirm = async (isCorrect) => {
    if (isCorrect) {
      await confirmPrediction(alertId, 'farmer-1', true, '')
      setStatus('submitted')
    } else {
      setStatus('wrong_selected')
    }
  }

  const handleSubmitWrong = async (e) => {
    e.preventDefault()
    await confirmPrediction(alertId, 'farmer-1', false, comment)
    setStatus('submitted')
  }

  if (status === 'submitted') {
    return (
      <div style={{ 
        marginTop: '0.75rem', 
        padding: '0.5rem 0.75rem', 
        backgroundColor: 'var(--color-surface)', 
        border: '1px solid var(--color-border)', 
        borderRadius: '2px',
        fontSize: '0.85rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>Feedback recorded.</span>
        <button 
          onClick={() => setStatus('idle')} 
          style={{ 
            background: 'none', 
            border: 'none', 
            color: 'var(--color-brand)', 
            cursor: 'pointer',
            padding: '0',
            minHeight: 'auto',
            minWidth: 'auto',
            textDecoration: 'underline',
            fontSize: '0.85rem'
          }}
        >
          Edit
        </button>
      </div>
    )
  }

  return (
    <div style={{ marginTop: '0.75rem' }}>
      {status === 'idle' && (
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => handleConfirm(true)}
            style={{
              backgroundColor: 'var(--color-brand)',
              color: '#FFFFFF',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              flex: 1
            }}
          >
            Confirm Correct
          </button>
          <button
            onClick={() => handleConfirm(false)}
            style={{
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-text-primary)',
              border: '1px solid var(--color-border)',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              flex: 1
            }}
          >
            Report Incorrect
          </button>
        </div>
      )}

      {status === 'wrong_selected' && (
        <form onSubmit={handleSubmitWrong} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
            Provide details (optional):
          </label>
          <input
            type="text"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Describe discrepancy"
            style={{
              padding: '0.5rem',
              border: '1px solid var(--color-border)'
            }}
          />
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="submit"
              style={{
                backgroundColor: 'var(--color-brand)',
                color: '#FFFFFF',
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                flex: 1
              }}
            >
              Submit Feedback
            </button>
            <button
              type="button"
              onClick={() => setStatus('idle')}
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                color: 'var(--color-text-secondary)',
                cursor: 'pointer',
                padding: '0.5rem'
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  )
}