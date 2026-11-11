import { useState } from 'react'
import { useCancelSensorRequestMutation, useRequestSensorMutation } from '../api/hooks'
import { buttonClass } from './ui/styles'

const when = (value) => (value ? new Date(value).toLocaleDateString('en-KE', { day: 'numeric', month: 'long', year: 'numeric' }) : '')

// Sensors are set up by an administrator, like a router installation: the farmer asks, an administrator arranges the visit.
export default function SensorSetupRow({ farm }) {
  const [asking, setAsking] = useState(false)
  const [note, setNote] = useState('')
  const request = useRequestSensorMutation()
  const cancel = useCancelSensorRequestMutation()
  const farmId = farm.farm_id || farm.id
  const status = farm.sensor_status || 'none'

  if (status === 'installed') {
    return <span className="font-normal">Sensor installed. Readings appear on your dashboard.</span>
  }

  if (status === 'in_progress') {
    return (
      <div className="flex flex-col items-start gap-2 font-normal">
        <span>An administrator has been in touch and is arranging the sensor visit.</span>
        <button type="button" disabled={cancel.isPending} onClick={() => cancel.mutate(farmId)} className={buttonClass({ variant: 'secondary', size: 'sm' })}>
          Cancel request
        </button>
        {cancel.isError && <span role="alert" className="text-small text-critical-text">Could not cancel the request. Please try again.</span>}
      </div>
    )
  }

  if (status === 'requested') {
    return (
      <div className="flex flex-col items-start gap-2 font-normal">
        <span>Sensor setup requested on {when(farm.sensor_requested_at)}. An administrator will contact you to arrange a visit.</span>
        <button type="button" disabled={cancel.isPending} onClick={() => cancel.mutate(farmId)} className={buttonClass({ variant: 'secondary', size: 'sm' })}>
          Cancel request
        </button>
        {cancel.isError && <span role="alert" className="text-small text-critical-text">Could not cancel the request. Please try again.</span>}
      </div>
    )
  }

  if (!asking) {
    return (
      <div className="flex flex-col items-start gap-2 font-normal">
        <span>Photo checks only. Sensors can be set up on your plot by an administrator.</span>
        <button type="button" onClick={() => setAsking(true)} className={buttonClass({ variant: 'secondary', size: 'sm' })}>Request sensor setup</button>
      </div>
    )
  }

  return (
    <form
      className="flex w-full flex-col items-start gap-2 font-normal"
      onSubmit={(event) => {
        event.preventDefault()
        request.mutate({ farmId, note }, { onSuccess: () => { setAsking(false); setNote('') } })
      }}
    >
      <label className="flex w-full flex-col gap-1 text-small text-ink">
        Anything the installer should know? (optional)
        <textarea
          value={note}
          onChange={(event) => setNote(event.target.value)}
          maxLength={300}
          rows={3}
          placeholder="For example: best days to visit, or how to find the plot"
          className="w-full rounded-control border-[1.5px] border-control bg-surface px-3 py-2 text-small text-ink"
        />
      </label>
      <div className="flex gap-2">
        <button type="submit" disabled={request.isPending} className={buttonClass({ size: 'sm' })}>Send request</button>
        <button type="button" onClick={() => setAsking(false)} className={buttonClass({ variant: 'secondary', size: 'sm' })}>Not now</button>
      </div>
      {request.isError && <span role="alert" className="text-small text-critical-text">Your request could not be sent. Please try again.</span>}
    </form>
  )
}
