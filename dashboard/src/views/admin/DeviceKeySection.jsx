import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createDeviceKey, getDeviceKey, revokeDeviceKey, useAdminManageMutation } from '../../api/adminManage'
import Notice from '../../components/ui/Notice'
import { buttonClass } from '../../components/ui/styles'

const when = (value) => (value ? new Date(value).toLocaleString('en-KE', { dateStyle: 'medium', timeStyle: 'short' }) : '')

// The installer creates a key for a plot's sensor box and types it into the box. The full key is shown once, here.
export default function DeviceKeySection({ farm }) {
  const qc = useQueryClient()
  const info = useQuery({ queryKey: ['admin', 'deviceKey', farm.id], queryFn: () => getDeviceKey(farm.id) })
  const create = useAdminManageMutation(createDeviceKey)
  const revoke = useAdminManageMutation(revokeDeviceKey)
  const [fresh, setFresh] = useState(null)
  const [copied, setCopied] = useState(false)
  const [asking, setAsking] = useState(false)
  const busy = create.isPending || revoke.isPending
  const failure = create.error || revoke.error || (info.isError && info.error)
  const hasKey = info.data?.has_key

  async function handleCreate() {
    setAsking(false)
    setCopied(false)
    try {
      setFresh(await create.mutateAsync({ id: farm.id }))
      qc.invalidateQueries({ queryKey: ['admin', 'deviceKey', farm.id] })
    } catch { /* The error is shown below. */ }
  }

  async function handleRevoke() {
    setAsking(false)
    setFresh(null)
    try {
      await revoke.mutateAsync({ id: farm.id })
    } catch { /* The error is shown below. */ }
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(fresh.key)
      setCopied(true)
    } catch { /* The key is also shown on screen to copy by hand. */ }
  }

  return (
    <section aria-labelledby="device-key-title" className="mt-6 border-t border-control pt-4">
      <h3 id="device-key-title" className="m-0 text-body font-bold text-ink">Sensor box key</h3>
      <p className="mb-3 mt-1 text-small text-ink-secondary">
        The sensor box at this plot sends its readings with this key. Create it when you install the box, then type it into the box.
      </p>
      {failure && <Notice tone="critical" className="mb-3"><p>{failure.message || 'That could not be done. Please try again.'}</p></Notice>}
      {fresh && (
        <Notice tone="warning" className="mb-3">
          <p className="m-0 font-bold">Copy this key now. It is shown only once.</p>
          <p className="my-2 break-all rounded-control bg-surface px-3 py-2 font-mono text-small text-ink" data-testid="new-device-key">{fresh.key}</p>
          <button type="button" onClick={copy} className={buttonClass({ variant: 'secondary', size: 'sm' })}>{copied ? 'Copied' : 'Copy key'}</button>
        </Notice>
      )}
      {!info.isLoading && (
        <p className="mb-3 mt-0 text-small text-ink">
          {hasKey
            ? <>A key is active (starts with <span className="font-mono">{info.data.prefix}</span>), made {when(info.data.created_at)}{info.data.created_by ? ` by ${info.data.created_by}` : ''}. {info.data.last_used_at ? `Last used ${when(info.data.last_used_at)}.` : 'Not used yet.'}</>
            : 'No key yet. The sensor box cannot send readings until you create one.'}
        </p>
      )}
      {asking ? (
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-small text-ink">{hasKey && !fresh ? 'The old key will stop working straight away.' : 'Stop the box from sending readings?'}</span>
          <button type="button" disabled={busy} onClick={asking === 'revoke' ? handleRevoke : handleCreate} className={buttonClass({ size: 'sm' })}>
            {asking === 'revoke' ? 'Yes, revoke it' : 'Yes, make a new key'}
          </button>
          <button type="button" onClick={() => setAsking(false)} className={buttonClass({ variant: 'secondary', size: 'sm' })}>Cancel</button>
        </div>
      ) : (
        <div className="flex flex-wrap gap-3">
          <button type="button" disabled={busy || info.isLoading} onClick={hasKey ? () => setAsking('create') : handleCreate} className={buttonClass({ variant: hasKey ? 'secondary' : 'primary', size: 'sm' })}>
            {hasKey ? 'Make a new key' : 'Create key'}
          </button>
          {hasKey && <button type="button" disabled={busy} onClick={() => setAsking('revoke')} className={buttonClass({ variant: 'secondary', size: 'sm' })}>Revoke key</button>}
        </div>
      )}
    </section>
  )
}
