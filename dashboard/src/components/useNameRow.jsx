import { useState } from 'react'
import { useUpdateProfileMutation } from '../api/hooks'
import { buttonClass, fieldClass, labelClass } from './ui/styles'

const NAME_MIN = 2
const NAME_MAX = 60

// The Name row of the account list, with an Edit button that turns it into a field.
// Same rules as the server: trimmed, 2 to 60 characters.
export default function useNameRow(name, onSaved) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(name || '')
  const [error, setError] = useState('')
  const update = useUpdateProfileMutation()

  const start = () => {
    setValue(name || '')
    setError('')
    setEditing(true)
  }

  const save = async (event) => {
    event.preventDefault()
    const trimmed = value.trim()
    if (trimmed.length < NAME_MIN || trimmed.length > NAME_MAX) {
      setError(`Your name must be between ${NAME_MIN} and ${NAME_MAX} characters.`)
      return
    }
    try {
      await update.mutateAsync({ name: trimmed })
      await onSaved()
      setEditing(false)
    } catch (err) {
      setError(err.message || 'Your name could not be saved. Please try again.')
    }
  }

  if (!editing) {
    return {
      label: 'Name',
      value: name || 'Not set',
      action: (
        <button type="button" onClick={start} className={buttonClass({ variant: 'quiet', size: 'sm' })}>
          Edit<span className="sr-only"> your name</span>
        </button>
      ),
    }
  }

  return {
    label: 'Name',
    value: (
      <form onSubmit={save} noValidate className="flex flex-col gap-3">
        <div>
          <label htmlFor="profile-name" className={labelClass}>Your name</label>
          <input
            id="profile-name"
            value={value}
            onChange={(event) => { setValue(event.target.value); setError('') }}
            autoComplete="name"
            maxLength={NAME_MAX + 20}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? 'profile-name-error' : 'profile-name-hint'}
            className={fieldClass}
            autoFocus
          />
          {error
            ? <p id="profile-name-error" role="alert" className="m-0 mt-2 text-small text-critical-text">{error}</p>
            : <p id="profile-name-hint" className="m-0 mt-2 text-small text-ink-secondary">{NAME_MIN} to {NAME_MAX} characters.</p>}
        </div>
        <div className="flex flex-wrap gap-3">
          <button type="submit" disabled={update.isPending} className={buttonClass({ size: 'sm' })}>
            {update.isPending ? 'Saving…' : 'Save name'}
          </button>
          <button type="button" onClick={() => setEditing(false)} className={buttonClass({ variant: 'secondary', size: 'sm' })}>
            Cancel
          </button>
        </div>
      </form>
    ),
  }
}
