import { useState } from 'react'
import { useAdminUsers } from '../../api/hooks'
import {
  archiveAdminFarm, createAdminFarm, resetAdminUserPassword, restoreAdminFarm, updateAdminFarm, updateAdminUser,
  useAdminAuditLog, useAdminManageMutation,
} from '../../api/adminManage'
import Badge from '../../components/ui/Badge'
import Card, { SectionHeader } from '../../components/ui/Card'
import DataTable from '../../components/ui/DataTable'
import Notice from '../../components/ui/Notice'
import Skeleton from '../../components/ui/Skeleton'
import Toolbar, { FilterSelect, SearchField } from '../../components/ui/Toolbar'
import { DATE_RANGES, inDateRange, uniqueOptions } from '../../components/ui/adminFilters'
import { buttonClass, focusRing } from '../../components/ui/styles'

const fieldClass = `mt-1 block min-h-11 w-full rounded-control border-[1.5px] border-control bg-surface px-3 text-small font-normal text-ink ${focusRing}`
const SOIL_TYPES = [['sandy_loam', 'Sandy loam'], ['loam', 'Loam'], ['silt_loam', 'Silt loam'], ['clay', 'Clay']]
const WATER_SOURCES = [['', 'Not recorded'], ['rain_fed', 'Rain only'], ['irrigated', 'Irrigated'], ['both', 'Both']]

function Field({ label, children }) {
  return <label className="text-small font-bold">{label}{children}</label>
}

// Edit a farmer's name and phone, or set a new password.
export function UserEditor({ user, onClose }) {
  const [form, setForm] = useState({ name: user.name, phone: user.phone })
  const [password, setPassword] = useState('')
  const [done, setDone] = useState('')
  const save = useAdminManageMutation(updateAdminUser)
  const reset = useAdminManageMutation(resetAdminUserPassword)

  async function handleSave(event) {
    event.preventDefault()
    setDone('')
    try {
      await save.mutateAsync({ id: user.id, data: { name: form.name, phone: form.phone } })
      setDone('Details saved.')
    } catch { /* The error is shown below. */ }
  }

  async function handleReset(event) {
    event.preventDefault()
    setDone('')
    try {
      await reset.mutateAsync({ id: user.id, password })
      setPassword('')
      setDone('Password changed. Tell the farmer the new password directly. It is not shown again.')
    } catch { /* The error is shown below. */ }
  }

  return (
    <Card aria-labelledby="user-editor-title">
      <SectionHeader id="user-editor-title" title={`Manage ${user.name}`} aside={<button type="button" onClick={onClose} className={buttonClass({ variant: 'quiet', size: 'sm' })}>Close</button>} />
      {done && <Notice tone="positive" className="mb-4"><p>{done}</p></Notice>}
      {(save.isError || reset.isError) && <Notice tone="critical" className="mb-4"><p>{(save.error || reset.error)?.message || 'That change could not be saved.'}</p></Notice>}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <form onSubmit={handleSave} className="flex flex-col gap-4">
          <Field label="Full name"><input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className={fieldClass} /></Field>
          <Field label="Phone number"><input required type="tel" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} className={fieldClass} /></Field>
          <button type="submit" disabled={save.isPending} className={buttonClass({ size: 'sm' })}>{save.isPending ? 'Saving…' : 'Save details'}</button>
        </form>
        <form onSubmit={handleReset} className="flex flex-col gap-4">
          <Field label="New password"><input required minLength={8} type="password" autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} className={fieldClass} /></Field>
          <p className="m-0 text-caption text-ink-secondary">At least 8 characters. The farmer's old password stops working straight away.</p>
          <button type="submit" disabled={reset.isPending} className={buttonClass({ variant: 'secondary', size: 'sm' })}>{reset.isPending ? 'Changing…' : 'Set new password'}</button>
        </form>
      </div>
    </Card>
  )
}

// Add a farm for a farmer (farm === null) or edit one. The NPK sensor setting can only be changed here.
export function FarmEditor({ farm, onClose }) {
  const users = useAdminUsers()
  const farmers = (users.data ?? []).filter((user) => user.role === 'farmer')
  const [owner, setOwner] = useState('')
  const [form, setForm] = useState({
    name: farm?.name ?? '',
    location: farm?.location ?? '',
    soil_type: farm?.soil_type ?? 'loam',
    size_acres: farm?.size_acres ?? '',
    planting_date: farm?.planting_date ?? '',
    water_source: farm?.water_source ?? '',
    seed_variety: farm?.seed_variety ?? '',
    has_npk_sensor: Boolean(farm?.has_npk_sensor),
  })
  const create = useAdminManageMutation(createAdminFarm)
  const update = useAdminManageMutation(updateAdminFarm)
  const archive = useAdminManageMutation(archiveAdminFarm)
  const restore = useAdminManageMutation(restoreAdminFarm)
  const busy = create.isPending || update.isPending || archive.isPending || restore.isPending
  const failure = create.error || update.error || archive.error || restore.error
  const set = (key) => (event) => setForm({ ...form, [key]: event.target.type === 'checkbox' ? event.target.checked : event.target.value })

  async function handleSubmit(event) {
    event.preventDefault()
    const data = {
      name: form.name.trim(),
      location: form.location.trim(),
      soil_type: form.soil_type,
      size_acres: form.size_acres === '' ? null : Number(form.size_acres),
      planting_date: form.planting_date || null,
      water_source: form.water_source || null,
      seed_variety: form.seed_variety.trim() || null,
      has_npk_sensor: form.has_npk_sensor,
    }
    try {
      if (farm) await update.mutateAsync({ id: farm.id, data })
      else await create.mutateAsync({ userId: owner, data })
      onClose()
    } catch { /* The error is shown below. */ }
  }

  async function handleArchive() {
    try {
      await (farm.deleted_at ? restore : archive).mutateAsync({ id: farm.id })
      onClose()
    } catch { /* The error is shown below. */ }
  }

  return (
    <Card aria-labelledby="farm-editor-title">
      <SectionHeader
        id="farm-editor-title"
        title={farm ? `Edit ${farm.name}` : 'Add a farm for a farmer'}
        aside={<button type="button" onClick={onClose} className={buttonClass({ variant: 'quiet', size: 'sm' })}>Close</button>}
      />
      {farm && <p className="mb-4 mt-0 text-small text-ink-secondary">Farmer: <span className="font-bold text-ink">{farm.owner_name}</span> {farm.owner_phone}</p>}
      {failure && <Notice tone="critical" className="mb-4"><p>{failure.message || 'That change could not be saved.'}</p></Notice>}
      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {!farm && (
          <Field label="Farmer">
            <select required value={owner} onChange={(event) => setOwner(event.target.value)} className={fieldClass}>
              <option value="">Choose a farmer</option>
              {farmers.map((user) => <option key={user.id} value={user.id}>{user.name} ({user.phone})</option>)}
            </select>
          </Field>
        )}
        <Field label="Farm name"><input required value={form.name} onChange={set('name')} className={fieldClass} /></Field>
        <Field label="County"><input required value={form.location} onChange={set('location')} className={fieldClass} /></Field>
        <Field label="Soil type">
          <select value={form.soil_type} onChange={set('soil_type')} className={fieldClass}>
            {SOIL_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </Field>
        <Field label="Size in acres"><input type="number" min="0.1" step="0.1" value={form.size_acres} onChange={set('size_acres')} className={fieldClass} /></Field>
        <Field label="Planting date"><input type="date" value={form.planting_date} onChange={set('planting_date')} className={fieldClass} /></Field>
        <Field label="Water source">
          <select value={form.water_source} onChange={set('water_source')} className={fieldClass}>
            {WATER_SOURCES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </Field>
        <Field label="Seed variety"><input value={form.seed_variety} onChange={set('seed_variety')} className={fieldClass} /></Field>
        <label className="flex min-h-11 cursor-pointer items-center gap-3 self-end text-small font-bold">
          <input type="checkbox" checked={form.has_npk_sensor} onChange={set('has_npk_sensor')} className="h-5 w-5 min-h-0 accent-brand" />
          This farm has an NPK sensor
        </label>
        <div className="flex flex-wrap gap-3 md:col-span-2">
          <button type="submit" disabled={busy} className={buttonClass({ size: 'sm' })}>{busy ? 'Saving…' : farm ? 'Save changes' : 'Add farm'}</button>
          {farm && (
            <button type="button" disabled={busy} onClick={handleArchive} className={buttonClass({ variant: 'secondary', size: 'sm' })}>
              {farm.deleted_at ? 'Restore this farm' : 'Archive this farm'}
            </button>
          )}
        </div>
      </form>
      {farm && !farm.deleted_at && <p className="mb-0 mt-3 text-caption text-ink-secondary">Archiving hides the farm from the farmer. Its readings and history are kept.</p>}
    </Card>
  )
}

const ACTION_LABELS = {
  'user.update': 'Edited farmer',
  'user.password_reset': 'Reset password',
  'farm.create': 'Added farm',
  'farm.update': 'Edited farm',
  'farm.archive': 'Archived farm',
  'farm.restore': 'Restored farm',
}
const FIELD_LABELS = {
  name: 'Name', phone: 'Phone', location: 'County', soil_type: 'Soil', size_acres: 'Size (acres)', planting_date: 'Planting date',
  water_source: 'Water source', seed_variety: 'Seed variety', has_npk_sensor: 'NPK sensor',
}
const showValue = (value) => (value === null || value === undefined || value === '' ? 'empty' : value === 'True' ? 'on' : value === 'False' ? 'off' : String(value).replaceAll('_', ' '))

// The permanent record of what administrators changed.
export function AuditPanel() {
  const log = useAdminAuditLog()
  const [search, setSearch] = useState('')
  const [action, setAction] = useState('all')
  const [admin, setAdmin] = useState('all')
  const [range, setRange] = useState('all')
  const entries = log.data ?? []
  const filtered = entries.filter((entry) => {
    if (action !== 'all' && entry.action !== action) return false
    if (admin !== 'all' && entry.admin_name !== admin) return false
    if (!inDateRange(entry.created_at, range)) return false
    return `${entry.admin_name} ${entry.target_label} ${ACTION_LABELS[entry.action] ?? entry.action}`.toLowerCase().includes(search.toLowerCase())
  })
  const adminOptions = uniqueOptions(entries, (entry) => entry.admin_name, (entry) => entry.admin_name, 'All administrators')
  const filtersOn = search || action !== 'all' || admin !== 'all' || range !== 'all'

  return (
    <Card aria-labelledby="audit-title">
      <SectionHeader id="audit-title" title="Activity log" aside={<Badge tone="neutral" size="sm" icon={false}>{filtered.length} of {entries.length} entries</Badge>} />
      <Toolbar>
        <SearchField label="Search the activity log" value={search} onChange={setSearch} placeholder="Search administrator, farmer, or farm" />
        <FilterSelect id="audit-action" label="Filter by action" value={action} onChange={setAction} options={[['all', 'All actions'], ...Object.entries(ACTION_LABELS)]} />
      </Toolbar>
      <Toolbar>
        <FilterSelect id="audit-admin" label="Filter by administrator" value={admin} onChange={setAdmin} options={adminOptions} />
        <FilterSelect id="audit-range" label="Filter by date" value={range} onChange={setRange} options={DATE_RANGES} />
      </Toolbar>
      {log.isError && <Notice tone="critical" className="mb-4"><p>The activity log could not be loaded. Check your admin access and connection.</p></Notice>}
      {log.isLoading ? <Skeleton label="Loading" className="h-24" /> : (
        <DataTable
          caption="Activity log"
          rows={filtered}
          rowKey={(entry) => entry.id}
          initialSort={{ key: 'when', dir: 'desc' }}
          empty={filtersOn ? 'No entries match those filters.' : 'No changes have been made by an administrator yet.'}
          columns={[
            { key: 'when', label: 'When', sortValue: (entry) => Date.parse(entry.created_at), render: (entry) => <span className="whitespace-nowrap text-ink-secondary">{new Date(entry.created_at).toLocaleString()}</span> },
            { key: 'admin', label: 'Administrator', sortValue: (entry) => entry.admin_name, render: (entry) => <span className="font-bold text-ink">{entry.admin_name}</span> },
            { key: 'action', label: 'Action', sortValue: (entry) => entry.action, render: (entry) => <span className="text-ink">{ACTION_LABELS[entry.action] ?? entry.action}</span> },
            { key: 'target', label: 'Who or what', sortValue: (entry) => entry.target_label, render: (entry) => <span className="text-ink">{entry.target_label}</span> },
            {
              key: 'changes', label: 'What changed',
              render: (entry) => {
                const items = Object.entries(entry.changes ?? {})
                if (!items.length) return <span className="text-caption text-ink-secondary">{entry.action === 'user.password_reset' ? 'A new password was set (not recorded)' : 'No details'}</span>
                return (
                  <ul className="m-0 list-none p-0 text-caption text-ink">
                    {items.map(([field, [from, to]]) => <li key={field}>{FIELD_LABELS[field] ?? field}: {showValue(from)} → {showValue(to)}</li>)}
                  </ul>
                )
              },
            },
          ]}
        />
      )}
      <p className="mb-0 mt-3 text-caption text-ink-secondary">This log can only be added to. Nothing in the app edits or deletes an entry.</p>
    </Card>
  )
}
