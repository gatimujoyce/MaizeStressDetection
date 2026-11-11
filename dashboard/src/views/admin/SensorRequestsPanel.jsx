import { useState } from 'react'
import { useAdminSensorRequests, useCancelAdminSensorRequestMutation, useMarkSensorContactedMutation, useMarkSensorInstalledMutation } from '../../api/hooks'
import Badge from '../../components/ui/Badge'
import Card, { SectionHeader } from '../../components/ui/Card'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import Notice from '../../components/ui/Notice'
import Skeleton from '../../components/ui/Skeleton'
import { buttonClass, linkClass } from '../../components/ui/styles'

const day = (value) => (value ? new Date(value).toLocaleDateString('en-KE', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Not set')
const words = (value) => (value ? String(value).replaceAll('_', ' ') : 'Not recorded')

// A request moves New -> In progress (contact with the farmer has begun) -> Completed (sensor installed).
const TABS = [
  { key: 'requested', label: 'New', empty: 'No new requests.' },
  { key: 'in_progress', label: 'In progress', empty: 'Nothing in progress. Start contact on a new request to move it here.' },
  { key: 'installed', label: 'Completed', empty: 'No completed installations yet.' },
]

function ConfirmDialog({ request, mode, onClose }) {
  const install = useMarkSensorInstalledMutation()
  const cancel = useCancelAdminSensorRequestMutation()
  const [npk, setNpk] = useState(Boolean(request.has_npk_sensor))
  const pending = install.isPending || cancel.isPending
  const failed = install.isError || cancel.isError

  if (mode === 'install') {
    return (
      <Modal title="Installation finished?" onClose={onClose}>
        <p className="m-0 text-body text-ink">
          Mark the sensor at <strong>{request.farm_name}</strong> ({request.farmer_name}) as installed. It moves to Completed.
        </p>
        <label className="mt-3 flex min-h-11 cursor-pointer items-center gap-2 text-small font-bold text-ink">
          <input type="checkbox" checked={npk} onChange={(event) => setNpk(event.target.checked)} className="h-4 w-4 min-h-0 accent-brand" />
          This plot also has an NPK (soil nutrient) sensor
        </label>
        {failed && <p role="alert" className="mb-0 mt-2 text-small text-critical-text">That did not work. Please try again.</p>}
        <div className="mt-4 flex gap-2">
          <button type="button" disabled={pending} onClick={() => install.mutate({ farmId: request.farm_id, hasNpkSensor: npk }, { onSuccess: onClose })} className={buttonClass({ size: 'sm' })}>
            Mark as installed
          </button>
          <button type="button" onClick={onClose} className={buttonClass({ variant: 'secondary', size: 'sm' })}>Not yet</button>
        </div>
      </Modal>
    )
  }
  return (
    <Modal title="Remove this request?" onClose={onClose}>
      <p className="m-0 text-body text-ink">
        Remove the request for <strong>{request.farm_name}</strong> ({request.farmer_name}) without installing a sensor. The farmer can ask again later.
      </p>
      {failed && <p role="alert" className="mb-0 mt-2 text-small text-critical-text">That did not work. Please try again.</p>}
      <div className="mt-4 flex gap-2">
        <button type="button" disabled={pending} onClick={() => cancel.mutate(request.farm_id, { onSuccess: onClose })} className={buttonClass({ size: 'sm' })}>Remove request</button>
        <button type="button" onClick={onClose} className={buttonClass({ variant: 'secondary', size: 'sm' })}>Keep it</button>
      </div>
    </Modal>
  )
}

function Tabs({ value, onChange, counts }) {
  return (
    <div role="radiogroup" aria-label="Request stage" className="mb-4 flex flex-wrap gap-2">
      {TABS.map((tab) => {
        const selected = tab.key === value
        return (
          <button
            key={tab.key}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(tab.key)}
            className={`min-h-11 rounded-control border-[1.5px] px-4 text-small font-bold ${selected ? 'border-brand bg-brand text-white' : 'border-control bg-surface text-ink'}`}
          >
            {tab.label} <span className="font-normal">({counts[tab.key] ?? 0})</span>
          </button>
        )
      })}
    </div>
  )
}

export default function SensorRequestsPanel() {
  const requests = useAdminSensorRequests()
  const contact = useMarkSensorContactedMutation()
  const [tab, setTab] = useState('requested')
  const [dialog, setDialog] = useState(null) // { request, mode }
  const all = requests.data ?? []
  const counts = all.reduce((acc, request) => ({ ...acc, [request.status]: (acc[request.status] ?? 0) + 1 }), {})
  const rows = all.filter((request) => request.status === tab)
  const current = TABS.find((item) => item.key === tab)

  const stageColumn = {
    key: 'stage', label: tab === 'installed' ? 'Installed' : 'Requested', sortValue: (r) => (tab === 'installed' ? r.installed_at : r.requested_at),
    render: (r) => (
      <>
        <span className="block text-ink">{tab === 'installed' ? day(r.installed_at) : day(r.requested_at)}</span>
        {tab === 'installed' && <span className="mt-0.5 block text-caption text-ink-secondary">Requested {day(r.requested_at)}</span>}
        {tab !== 'requested' && r.contacted_at && <span className="mt-0.5 block text-caption text-ink-secondary">Contact began {day(r.contacted_at)}</span>}
        {r.note && <span className="mt-0.5 block max-w-56 text-caption text-ink-secondary">“{r.note}”</span>}
      </>
    ),
  }

  const columns = [
    {
      key: 'farmer', label: 'Farmer', sortValue: (r) => r.farmer_name,
      render: (r) => (
        <>
          <span className="block font-bold text-ink">{r.farmer_name}</span>
          <a href={`tel:${r.farmer_phone}`} className={`mt-0.5 block text-caption tabular-nums ${linkClass}`}>{r.farmer_phone}</a>
        </>
      ),
    },
    {
      key: 'plot', label: 'Plot', sortValue: (r) => r.farm_name,
      render: (r) => (
        <>
          <span className="block font-bold text-ink">{r.farm_name}</span>
          <span className="mt-0.5 block text-caption text-ink-secondary">{r.location}{r.size_acres ? ` · ${r.size_acres} acres` : ''}</span>
          {r.latitude != null && r.longitude != null && (
            <span className="mt-0.5 block text-caption tabular-nums text-ink-secondary">{r.latitude.toFixed(5)}, {r.longitude.toFixed(5)}</span>
          )}
        </>
      ),
    },
    {
      key: 'land', label: 'Land and crop',
      render: (r) => (
        <>
          <span className="block capitalize text-ink">{words(r.soil_type)}</span>
          <span className="mt-0.5 block text-caption text-ink-secondary">Planted: {day(r.planting_date)}</span>
          <span className="mt-0.5 block text-caption text-ink-secondary">Water: {r.water_source || 'Not recorded'} · Seed: {r.seed_variety || 'Not recorded'}</span>
        </>
      ),
    },
    stageColumn,
  ]
  if (tab === 'installed') {
    columns.push({ key: 'npk', label: 'NPK sensor', render: (r) => (r.has_npk_sensor ? <Badge tone="healthy" size="sm" icon={false}>Yes</Badge> : <span className="text-ink-secondary">No</span>) })
  } else {
    columns.push({
      key: 'actions', label: '',
      render: (r) => (
        <div className="flex flex-wrap gap-2">
          {tab === 'requested' && (
            <button type="button" disabled={contact.isPending} onClick={() => contact.mutate(r.farm_id)} className={buttonClass({ size: 'sm' })}>Start contact</button>
          )}
          <button type="button" onClick={() => setDialog({ request: r, mode: 'install' })} className={buttonClass({ variant: tab === 'requested' ? 'secondary' : 'primary', size: 'sm' })}>Mark installed</button>
          <button type="button" onClick={() => setDialog({ request: r, mode: 'cancel' })} className={buttonClass({ variant: 'secondary', size: 'sm' })}>Remove</button>
        </div>
      ),
    })
  }

  return (
    <Card aria-labelledby="sensor-requests-title">
      <SectionHeader
        id="sensor-requests-title"
        title="Sensor setup requests"
        aside={<Badge tone={counts.requested ? 'warning' : 'neutral'} size="sm" icon={false}>{counts.requested ?? 0} new</Badge>}
      />
      {requests.isError && <Notice tone="critical" className="mb-4"><p>Sensor requests could not be loaded.</p></Notice>}
      {contact.isError && <Notice tone="critical" className="mb-4"><p>Could not update that request. Please try again.</p></Notice>}
      <Tabs value={tab} onChange={setTab} counts={counts} />
      {requests.isLoading ? <Skeleton label="Loading" className="h-24" /> : (
        <DataTable
          key={tab}
          caption={`${current.label} sensor requests`}
          rows={rows}
          rowKey={(request) => request.farm_id}
          initialSort={{ key: 'stage', dir: tab === 'installed' ? 'desc' : 'asc' }}
          empty={current.empty}
          columns={columns}
        />
      )}
      {dialog && <ConfirmDialog key={`${dialog.mode}-${dialog.request.farm_id}`} request={dialog.request} mode={dialog.mode} onClose={() => setDialog(null)} />}
    </Card>
  )
}
