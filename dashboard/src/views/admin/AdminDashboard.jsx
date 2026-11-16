import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAdminFarms, useAdminFeedback, useAdminModelVersions, useAdminRetrainingJobs, useAdminSmsLog, useAdminUsers, useCreateAdminUserMutation, useRequestAdminRetrainMutation, useSetAdminModelVersionActiveMutation } from '../../api/hooks'
import Badge from '../../components/ui/Badge'
import Card, { SectionHeader } from '../../components/ui/Card'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import Notice from '../../components/ui/Notice'
import PageHeader from '../../components/ui/PageHeader'
import StatStrip from '../../components/ui/StatStrip'
import Toolbar, { FilterCheckbox, FilterSelect, SearchField } from '../../components/ui/Toolbar'
import { adminFieldClass, adminLabelClass, buttonClass, linkClass } from '../../components/ui/styles'
import { DATE_RANGES, inDateRange, uniqueOptions } from '../../components/ui/adminFilters'
import { formatDateTime, formatDay } from '../../content/dates'
import AdminProfile from './AdminProfile'
import AdminShell from './AdminShell'
import SensorRequestsPanel from './SensorRequestsPanel'
import TableCard from './TableCard'
import { AuditPanel, FarmEditor, UserEditor } from './ManagePanels'

const SECTIONS = {
  overview: { title: 'Overview', description: 'Farms, accounts and text messages at a glance.', Panel: AdminOverview },
  farms: { title: 'Farms', description: 'Every registered farm, its farmer and its sensors.', Panel: FarmsPanel },
  sensors: { title: 'Sensor requests', description: 'Farmers who asked for a sensor to be set up on their plot.', Panel: SensorRequestsPanel },
  users: { title: 'Users', description: 'Farmer and administrator accounts.', Panel: UsersPanel },
  feedback: { title: 'Feedback', description: 'What farmers said about their results.', Panel: FeedbackPanel },
  models: { title: 'Model versions', description: 'Registered model versions and which one is in use.', Panel: ModelsPanel },
  retraining: { title: 'Retraining', description: 'Retraining runs and their quality checks.', Panel: RetrainingPanel },
  sms: { title: 'SMS log', description: 'Text messages sent to farmers, and whether they arrived.', Panel: SmsPanel },
  audit: { title: 'Activity log', description: 'A permanent record of what administrators changed, and when.', Panel: AuditPanel },
  profile: { title: 'Profile', description: 'Your account.', Panel: AdminProfile },
}

// Small status label inside a table cell.
function Tag({ children, tone = 'neutral' }) {
  return <Badge tone={tone} size="sm" icon={false}>{children}</Badge>
}

const timeValue = (value) => (value ? Date.parse(value) || null : null)
const When = ({ value }) => <span className="whitespace-nowrap tabular-nums text-ink-secondary">{formatDateTime(value)}</span>

export default function AdminDashboard() {
  const [searchParams] = useSearchParams()
  const requestedSection = searchParams.get('view')
  const activeSection = Object.hasOwn(SECTIONS, requestedSection) ? requestedSection : 'overview'
  const { title, description, Panel } = SECTIONS[activeSection]

  return (
    <AdminShell activeSection={activeSection}>
      <div className="flex flex-col gap-stack">
        <PageHeader title={title} subtitle={description} />
        <Panel />
      </div>
    </AdminShell>
  )
}

function AdminOverview() {
  const farms = useAdminFarms()
  const users = useAdminUsers()
  const smsLog = useAdminSmsLog()
  const userRows = users.data ?? []
  const smsRows = smsLog.data ?? []
  const smsCount = (status) => smsRows.filter((entry) => entry.status?.toLowerCase() === status).length
  const farmerCount = userRows.filter((user) => user.role === 'farmer').length
  const adminCount = userRows.filter((user) => user.role === 'admin').length
  const farmRows = farms.data ?? []

  return (
    <>
      <StatStrip
        label="Admin overview counts"
        stats={[
          { label: 'Registered farms', value: farmRows.length, isLoading: farms.isLoading, isError: farms.isError },
          {
            label: 'User accounts', value: userRows.length, isLoading: users.isLoading, isError: users.isError,
            detail: `${farmerCount} ${farmerCount === 1 ? 'farmer' : 'farmers'} · ${adminCount} ${adminCount === 1 ? 'admin' : 'admins'}`,
          },
          {
            label: 'SMS alert records', value: smsRows.length, isLoading: smsLog.isLoading, isError: smsLog.isError,
            detail: `${smsCount('sent')} sent · ${smsCount('failed')} failed · ${smsCount('pending')} pending`,
          },
        ]}
      />
      {(users.isError || smsLog.isError) && (
        <Notice tone="critical" onRetry={() => { users.refetch(); smsLog.refetch() }} retrying={users.isFetching || smsLog.isFetching}>
          <p>Some overview counts could not be loaded. Check your connection or access.</p>
        </Notice>
      )}
      <TableCard
        id="recent-farms-title"
        title="Registered farms"
        aside={<span className="text-small tabular-nums text-ink-secondary">{farmRows.length} total</span>}
        query={farms}
        errorText="Farm records could not be loaded."
        footer={farmRows.length > 5 && (
          <Link to="/admin?view=farms" className={`inline-flex min-h-11 items-center ${linkClass}`}>All {farmRows.length} farms</Link>
        )}
      >
        <DataTable
          flush
          wide={false}
          caption="Registered farms, first five"
          rows={farmRows.slice(0, 5)}
          rowKey={(farm) => farm.id}
          empty="No farms have been registered yet."
          columns={[
            { key: 'name', label: 'Farm', render: (farm) => <span className="font-bold text-ink">{farm.name}</span> },
            { key: 'owner', label: 'Farmer', render: (farm) => <span className="text-ink">{farm.owner_name || 'Unknown farmer'}</span> },
            { key: 'location', label: 'Location', render: (farm) => <span className="text-ink-secondary">{farm.location}</span> },
            { key: 'soil', label: 'Soil', render: (farm) => <span className="capitalize text-ink-secondary">{farm.soil_type?.replaceAll('_', ' ') || 'Not recorded'}</span> },
          ]}
        />
      </TableCard>
    </>
  )
}

function AddAdminDialog({ onClose, onCreated }) {
  const createAdmin = useCreateAdminUserMutation()
  const [form, setForm] = useState({ name: '', phone: '', password: '' })

  async function handleSubmit(event) {
    event.preventDefault()
    try {
      const result = await createAdmin.mutateAsync(form)
      onCreated(result.name)
      onClose()
    } catch { /* Mutation state displays the API error below. */ }
  }

  return (
    <Modal title="Add an administrator" onClose={onClose}>
      <p className="mb-4 mt-0 text-small text-ink-secondary">Create a separate admin login for a trusted team member.</p>
      {createAdmin.isError && <Notice tone="critical" className="mb-4"><p>{createAdmin.error?.message || 'Could not create the administrator. Check whether the phone is already registered.'}</p></Notice>}
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <label className={adminLabelClass}>Full name<input required autoComplete="name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className={adminFieldClass} /></label>
        <label className={adminLabelClass}>Kenyan phone number<input required type="tel" autoComplete="tel" placeholder="07… or +254…" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} className={adminFieldClass} /></label>
        <div>
          <label className={adminLabelClass}>Temporary password<input required minLength={8} type="password" autoComplete="new-password" aria-describedby="temp-password-hint" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} className={adminFieldClass} /></label>
          <p id="temp-password-hint" className="m-0 mt-2 text-small text-ink-secondary">At least 8 characters. They must choose their own password the first time they sign in.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button disabled={createAdmin.isPending} type="submit" className={buttonClass({ size: 'sm' })}>{createAdmin.isPending ? 'Creating account…' : 'Create admin account'}</button>
          <button type="button" onClick={onClose} className={buttonClass({ variant: 'secondary', size: 'sm' })}>Cancel</button>
        </div>
      </form>
    </Modal>
  )
}

function UsersPanel() {
  const users = useAdminUsers()
  const [search, setSearch] = useState('')
  const [adding, setAdding] = useState(false)
  const [createdName, setCreatedName] = useState('')
  const [managedId, setManagedId] = useState(null)
  const managed = (users.data ?? []).find((user) => user.id === managedId)
  const filteredUsers = (users.data ?? []).filter((user) => `${user.name} ${user.phone} ${user.role}`.toLowerCase().includes(search.toLowerCase()))

  return (
    <TableCard
      id="users-title"
      title="People with access"
      aside={<span className="text-small tabular-nums text-ink-secondary">{users.data?.length ?? 0} accounts</span>}
      query={users}
      errorText="Could not load users. Check your admin access and connection."
      toolbar={(
        <Toolbar action={<button type="button" onClick={() => { setCreatedName(''); setAdding(true) }} className={buttonClass({ size: 'sm' })}>Add an administrator</button>}>
          <SearchField label="Search users" value={search} onChange={setSearch} placeholder="Search name, phone, or role" />
        </Toolbar>
      )}
      notices={createdName && <Notice tone="positive"><p>Administrator account created for {createdName}.</p></Notice>}
    >
      <DataTable
        flush
        wide={false}
        caption="User accounts"
        rows={filteredUsers}
        rowKey={(user) => user.id}
        initialSort={{ key: 'name', dir: 'asc' }}
        empty={search ? 'No accounts match this search.' : 'No accounts found.'}
        columns={[
          {
            key: 'name', label: 'Name', sortValue: (user) => user.name,
            render: (user) => (
              <>
                <span className="block whitespace-nowrap font-bold text-ink">{user.name}</span>
                {/* Under 640px the Phone and Role columns are left out, so they show here instead. */}
                <span className="block whitespace-nowrap tabular-nums text-ink-secondary sm:hidden">{user.phone}</span>
                <span className="mt-1 block sm:hidden"><Tag tone={user.role === 'admin' ? 'healthy' : 'neutral'}><span className="capitalize">{user.role}</span></Tag></span>
              </>
            ),
          },
          { key: 'phone', label: 'Phone', hideBelowSm: true, sortValue: (user) => user.phone, render: (user) => <span className="whitespace-nowrap tabular-nums text-ink-secondary">{user.phone}</span> },
          { key: 'role', label: 'Role', hideBelowSm: true, sortValue: (user) => user.role, render: (user) => <Tag tone={user.role === 'admin' ? 'healthy' : 'neutral'}><span className="capitalize">{user.role}</span></Tag> },
          {
            key: 'manage', label: '',
            render: (user) => user.role === 'farmer'
              ? <button type="button" onClick={() => setManagedId(user.id)} className={`-my-3 ${buttonClass({ variant: 'quiet', size: 'sm' })}`}>Manage<span className="sr-only"> {user.name}</span></button>
              : null,
          },
        ]}
      />
      {adding && <AddAdminDialog onClose={() => setAdding(false)} onCreated={setCreatedName} />}
      {managed && <UserEditor key={managed.id} user={managed} onClose={() => setManagedId(null)} />}
    </TableCard>
  )
}

function FarmsPanel() {
  const [includeDeleted, setIncludeDeleted] = useState(false)
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState(null) // a farm, 'new', or null
  const farms = useAdminFarms(includeDeleted)
  const visibleFarms = (farms.data ?? []).filter((farm) => {
    const fields = [farm.name, farm.owner_name, farm.owner_phone, farm.location, farm.soil_type, farm.seed_variety, farm.water_source]
    return fields.filter(Boolean).join(' ').toLowerCase().includes(search.toLowerCase())
  })

  return (
    <TableCard
      id="farms-title"
      title="Registered farms"
      aside={<span className="text-small tabular-nums text-ink-secondary">{farms.data?.length ?? 0} {includeDeleted ? 'records' : 'active farms'}</span>}
      query={farms}
      errorText="Farm records could not be loaded. Check your admin access and connection."
      toolbar={(
        <Toolbar action={<button type="button" onClick={() => setEditing('new')} className={buttonClass({ size: 'sm' })}>Add a farm</button>}>
          <SearchField label="Search farms" value={search} onChange={setSearch} placeholder="Search farm, farmer, location, crop, or soil" />
          <FilterCheckbox label="Include archived farms" checked={includeDeleted} onChange={setIncludeDeleted} />
        </Toolbar>
      )}
      footer={`Showing ${visibleFarms.length} of ${farms.data?.length ?? 0} returned records.`}
    >
      <DataTable
        flush
        caption="Registered farms"
        rows={visibleFarms}
        rowKey={(farm) => farm.id}
        initialSort={{ key: 'name', dir: 'asc' }}
        empty={search ? 'No farms match this search.' : 'No farm records found.'}
        columns={[
          {
            key: 'name', label: 'Farm', sortValue: (farm) => farm.name,
            render: (farm) => <><span className="block whitespace-nowrap font-bold text-ink">{farm.name}</span><span className="block whitespace-nowrap text-caption text-ink-secondary">{farm.size_acres ? `${farm.size_acres} acres` : 'Size not set'}</span></>,
          },
          {
            key: 'owner', label: 'Farmer', sortValue: (farm) => farm.owner_name,
            render: (farm) => <><span className="block whitespace-nowrap font-bold text-ink">{farm.owner_name || 'Unknown farmer'}</span><span className="block whitespace-nowrap text-caption tabular-nums text-ink-secondary">{farm.owner_phone}</span></>,
          },
          { key: 'location', label: 'Location', sortValue: (farm) => farm.location, render: (farm) => <span className="text-ink-secondary">{farm.location}</span> },
          {
            key: 'land', label: 'Land', sortValue: (farm) => farm.soil_type,
            render: (farm) => <><span className="block whitespace-nowrap capitalize text-ink">{farm.soil_type?.replaceAll('_', ' ') || 'Not recorded'}</span>{farm.planting_date && <span className="block whitespace-nowrap text-caption text-ink-secondary">Planted {formatDay(farm.planting_date)}</span>}</>,
          },
          {
            key: 'crop', label: 'Crop and water', sortValue: (farm) => farm.seed_variety,
            render: (farm) => <><span className="block text-ink">Seed: {farm.seed_variety || 'Not recorded'}</span><span className="block text-caption text-ink-secondary">Water: {farm.water_source || 'Not recorded'}</span></>,
          },
          {
            key: 'status', label: 'Status', sortValue: (farm) => (farm.deleted_at ? 'Archived' : 'Active'),
            render: (farm) => (farm.deleted_at ? <Tag>Archived</Tag> : <Tag tone="healthy">Active</Tag>),
          },
          {
            key: 'npk', label: 'NPK sensor', sortValue: (farm) => (farm.has_npk_sensor ? 1 : 0),
            render: (farm) => (farm.has_npk_sensor ? <Tag tone="healthy">On</Tag> : <span className="text-ink-secondary">Off</span>),
          },
          {
            key: 'edit', label: '',
            render: (farm) => <button type="button" onClick={() => setEditing(farm)} className={`-my-3 ${buttonClass({ variant: 'quiet', size: 'sm' })}`}>Edit<span className="sr-only"> {farm.name}</span></button>,
          },
        ]}
      />
      {editing && <FarmEditor key={editing === 'new' ? 'new' : editing.id} farm={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />}
    </TableCard>
  )
}

const MATCH_LABELS = { yes: 'Matched what they saw', partly: 'Partly matched', no: 'Did not match' }
const ACTION_LABELS = { followed: 'Followed the advice', other: 'Did something else', none: 'Has not acted yet' }
const OUTCOME_LABELS = { better: 'Field got better', same: 'No change', worse: 'Field got worse', not_acted: 'Did not act' }
const MATCH_TONES = { yes: 'healthy', partly: 'warning', no: 'critical' }

function FeedbackPanel() {
  const feedback = useAdminFeedback()
  const [filter, setFilter] = useState('all')
  const [farmFilter, setFarmFilter] = useState('all')
  const [search, setSearch] = useState('')
  const rows = feedback.data ?? []
  const farmOptions = uniqueOptions(rows, (item) => item.farm_id, (item) => `${item.farm_name} (${item.farmer_name})`, 'All farms')
  const inaccurateCount = rows.filter((item) => !item.accurate).length
  const matchedCount = rows.filter((item) => item.matched === 'yes' || (item.matched == null && item.accurate)).length
  const actedCount = rows.filter((item) => item.action_taken === 'followed' || item.action_taken === 'other').length
  const followUps = rows.filter((item) => item.follow_up_outcome)
  const betterCount = followUps.filter((item) => item.follow_up_outcome === 'better').length
  const filtered = rows.filter((item) => {
    if (filter === 'inaccurate' && item.accurate) return false
    if (filter === 'acted' && item.action_taken !== 'followed' && item.action_taken !== 'other') return false
    if (farmFilter !== 'all' && item.farm_id !== farmFilter) return false
    return `${item.correct_label ?? ''} ${item.comment ?? ''} ${item.farm_name ?? ''} ${item.farmer_name ?? ''} ${item.disease_label ?? ''}`.toLowerCase().includes(search.toLowerCase())
  })
  const state = { isLoading: feedback.isLoading, isError: feedback.isError }

  return (
    <>
      <StatStrip
        label="Feedback summary"
        stats={[
          { label: 'Responses received', value: rows.length, ...state },
          { label: 'Matched what they saw', value: rows.length ? `${Math.round((100 * matchedCount) / rows.length)}%` : '–', detail: `${matchedCount} of ${rows.length} results`, ...state },
          { label: 'Acted on the advice', value: actedCount, detail: `of ${rows.length} responses`, ...state },
          { label: 'Better after a week', value: followUps.length ? `${betterCount} of ${followUps.length}` : '–', detail: followUps.length ? 'follow-up answers' : 'no follow-ups answered yet', ...state },
        ]}
      />
      <TableCard
        id="feedback-title"
        title="Prediction feedback"
        aside={<Tag tone={inaccurateCount ? 'warning' : 'neutral'}>{inaccurateCount} flagged inaccurate</Tag>}
        query={feedback}
        errorText="Feedback could not be loaded. Check your admin access and connection."
        toolbar={(
          <Toolbar>
            <SearchField label="Search feedback" value={search} onChange={setSearch} placeholder="Search farm, farmer, comment, or result" />
            <FilterSelect id="feedback-filter" label="Filter feedback" value={filter} onChange={setFilter} options={[['all', 'All feedback'], ['inaccurate', 'Did not fully match'], ['acted', 'Acted on the advice']]} />
            <FilterSelect id="feedback-farm-filter" label="Filter by farm" value={farmFilter} onChange={setFarmFilter} options={farmOptions} />
          </Toolbar>
        )}
      >
        <DataTable
          flush
          caption="Prediction feedback"
          rows={filtered}
          rowKey={(item) => item.id}
          initialSort={{ key: 'when', dir: 'desc' }}
          empty={search || filter !== 'all' || farmFilter !== 'all' ? 'No feedback matches those filters.' : 'No farmer feedback has been submitted yet.'}
          columns={[
            { key: 'when', label: 'When', sortValue: (item) => timeValue(item.created_at), render: (item) => <When value={item.created_at} /> },
            {
              key: 'who', label: 'Farmer and farm', sortValue: (item) => item.farmer_name,
              render: (item) => <><span className="block font-bold text-ink">{item.farmer_name}</span><span className="block text-caption text-ink-secondary">{item.farm_name}</span></>,
            },
            { key: 'result', label: 'Result', sortValue: (item) => item.disease_label, render: (item) => <span className="capitalize text-ink">{item.disease_label ? item.disease_label.replaceAll('_', ' ') : 'Not recorded'}</span> },
            {
              key: 'matched', label: 'Matched', sortValue: (item) => item.matched ?? (item.accurate ? 'yes' : 'no'),
              render: (item) => <Tag tone={MATCH_TONES[item.matched] ?? (item.accurate ? 'healthy' : 'critical')}>{MATCH_LABELS[item.matched] ?? (item.accurate ? 'Prediction accurate' : 'Marked inaccurate')}</Tag>,
            },
            { key: 'action', label: 'Acted', sortValue: (item) => item.action_taken, render: (item) => <span className="text-ink-secondary">{ACTION_LABELS[item.action_taken] ?? 'Not answered'}</span> },
            {
              key: 'outcome', label: 'After a week', sortValue: (item) => item.follow_up_outcome,
              render: (item) => (item.follow_up_outcome
                ? <Tag tone={item.follow_up_outcome === 'better' ? 'healthy' : item.follow_up_outcome === 'worse' ? 'critical' : 'neutral'}>{OUTCOME_LABELS[item.follow_up_outcome]}</Tag>
                : <span className="text-ink-secondary">Not yet</span>),
            },
            {
              key: 'note', label: 'What the farmer said',
              render: (item) => (
                <span className="block max-w-xs text-ink">
                  {item.correct_label && <span className="block"><span className="font-bold">Thinks it is:</span> {String(item.correct_label).replaceAll('_', ' ')}</span>}
                  {item.comment && <span className="block text-ink-secondary">“{item.comment}”</span>}
                  {!item.correct_label && !item.comment && <span className="text-ink-secondary">Nothing added</span>}
                </span>
              ),
            },
          ]}
        />
      </TableCard>
    </>
  )
}

const formatMetric = (value) => (typeof value === 'number' ? (value <= 1 ? `${(value * 100).toFixed(1)}%` : value.toFixed(2)) : String(value))

function ModelsPanel() {
  const versions = useAdminModelVersions()
  const setActive = useSetAdminModelVersionActiveMutation()
  const [search, setSearch] = useState('')
  const records = versions.data ?? []
  const modelNames = [...new Set(records.map((item) => item.model_name))]
  const filtered = records.filter((item) => `${item.model_name} ${item.version} ${Object.keys(item.metrics ?? {}).join(' ')}`.toLowerCase().includes(search.toLowerCase()))
  const activeTotal = records.filter((item) => item.is_active).length
  const state = { isLoading: versions.isLoading, isError: versions.isError }

  return (
    <>
      <StatStrip
        label="Model version summary"
        stats={[
          { label: 'Model families', value: modelNames.length, ...state },
          { label: 'Registered versions', value: records.length, ...state },
          { label: 'Active deployments', value: activeTotal, ...state },
        ]}
      />
      <TableCard
        id="models-title"
        title="Model versions"
        aside={<Tag tone={activeTotal ? 'healthy' : 'neutral'}>{activeTotal} active</Tag>}
        query={versions}
        errorText="Model versions could not be loaded. Check your admin access and connection."
        toolbar={(
          <Toolbar>
            <SearchField label="Search model versions" value={search} onChange={setSearch} placeholder="Search model, version, or metric" />
          </Toolbar>
        )}
        notices={setActive.isError && <Notice tone="critical"><p>{setActive.error?.message || 'The deployment status could not be updated.'}</p></Notice>}
        footer={modelNames.length > 1 && 'Activating a version replaces the active version for that model family.'}
      >
        <DataTable
          flush
          caption="Model versions"
          rows={filtered}
          rowKey={(item) => item.id}
          initialSort={{ key: 'model', dir: 'asc' }}
          empty={search ? 'No model versions match this search.' : 'No model versions have been registered yet.'}
          columns={[
            { key: 'model', label: 'Model', sortValue: (item) => item.model_name, render: (item) => <span className="font-bold capitalize text-ink">{item.model_name}</span> },
            { key: 'version', label: 'Version', sortValue: (item) => item.version, render: (item) => <span className="whitespace-nowrap text-ink">{item.version}</span> },
            {
              key: 'metrics', label: 'Evaluation metrics',
              render: (item) => {
                const entries = Object.entries(item.metrics ?? {})
                if (!entries.length) return <span className="text-ink-secondary">No metrics recorded</span>
                return (
                  <dl className="m-0 grid grid-cols-[auto_auto] gap-x-4 gap-y-1">
                    {entries.map(([key, value]) => (
                      <div key={key} className="contents">
                        <dt className="capitalize text-ink-secondary">{key.replaceAll('_', ' ')}</dt>
                        <dd className="m-0 text-right tabular-nums text-ink">{formatMetric(value)}</dd>
                      </div>
                    ))}
                  </dl>
                )
              },
            },
            { key: 'status', label: 'Status', sortValue: (item) => (item.is_active ? 0 : 1), render: (item) => (item.is_active ? <Tag tone="healthy">Active</Tag> : <Tag>Standby</Tag>) },
            {
              key: 'activate', label: '',
              render: (item) => (item.is_active ? null : (
                <button
                  type="button"
                  disabled={setActive.isPending}
                  onClick={() => setActive.mutate({ versionId: item.id, isActive: true })}
                  className={`whitespace-nowrap ${buttonClass({ variant: 'secondary', size: 'sm' })}`}
                >
                  {setActive.isPending ? 'Updating deployment…' : 'Set as active version'}
                </button>
              )),
            },
          ]}
        />
      </TableCard>
    </>
  )
}

const MODEL_FAMILIES = [['triage', 'Triage'], ['disease', 'Disease'], ['nutrient', 'Nutrient'], ['sensor', 'Sensor']]

function RetrainingPanel() {
  const [modelName, setModelName] = useState('triage')
  const jobs = useAdminRetrainingJobs()
  const requestRun = useRequestAdminRetrainMutation()
  const [requestResult, setRequestResult] = useState(null)
  const sortedJobs = [...(jobs.data ?? [])].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  const deployed = sortedJobs.filter((job) => job.deployed).length
  const passed = sortedJobs.filter((job) => job.passed_gate).length
  const state = { isLoading: jobs.isLoading, isError: jobs.isError }

  async function handleRequest(event) {
    event.preventDefault()
    setRequestResult(null)
    try {
      setRequestResult(await requestRun.mutateAsync(modelName))
    } catch { /* Mutation error appears below the form. */ }
  }

  return (
    <>
      <StatStrip
        label="Retraining summary"
        stats={[
          { label: 'Recorded runs', value: sortedJobs.length, ...state },
          { label: 'Passed quality gate', value: passed, ...state },
          { label: 'Deployed outcomes', value: deployed, ...state },
        ]}
      />
      <Card aria-labelledby="request-title">
        <SectionHeader
          id="request-title"
          title="Request retraining"
          description="The server confirms it received the request. The history below shows the runs the backend has recorded."
        />
        <form onSubmit={handleRequest} className="flex flex-wrap items-end gap-3">
          <label className={`${adminLabelClass} min-w-0 flex-1 basis-48 sm:flex-none`}>
            Model family
            <select value={modelName} onChange={(event) => setModelName(event.target.value)} className={adminFieldClass}>
              {MODEL_FAMILIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <button type="submit" disabled={requestRun.isPending} className={buttonClass({ size: 'sm' })}>{requestRun.isPending ? 'Submitting request…' : 'Request retraining'}</button>
        </form>
        {requestResult && (
          <Notice tone="positive" title="Request accepted" className="mt-4">
            <p>{requestResult.model_name} · {requestResult.status} · Job ID {requestResult.job_id}</p>
          </Notice>
        )}
        {requestRun.isError && <Notice tone="critical" className="mt-4"><p>{requestRun.error?.message || 'The retraining request could not be submitted.'}</p></Notice>}
      </Card>
      <TableCard
        id="history-title"
        title="Quality and deployment"
        aside={<span className="text-small tabular-nums text-ink-secondary">{passed} passed · {deployed} deployed</span>}
        query={jobs}
        errorText="Retraining history could not be loaded. Check your admin access and connection."
      >
        <DataTable
          flush
          caption="Retraining run history"
          rows={sortedJobs}
          rowKey={(job) => job.id}
          initialSort={{ key: 'created', dir: 'desc' }}
          empty="No retraining history has been recorded yet."
          columns={[
            { key: 'model', label: 'Model', sortValue: (job) => job.model_name, render: (job) => <span className="font-bold capitalize text-ink">{job.model_name}</span> },
            { key: 'created', label: 'Requested', sortValue: (job) => timeValue(job.created_at), render: (job) => <When value={job.created_at} /> },
            { key: 'gate', label: 'Quality gate', sortValue: (job) => (job.passed_gate ? 1 : 0), render: (job) => <Tag tone={job.passed_gate ? 'healthy' : 'critical'}>{job.passed_gate ? 'Quality gate passed' : 'Quality gate failed'}</Tag> },
            { key: 'deployed', label: 'Deployed', sortValue: (job) => (job.deployed ? 1 : 0), render: (job) => <span className="text-ink-secondary">{job.deployed ? 'Deployed' : 'Not deployed'}</span> },
            { key: 'old', label: 'Previous metrics', render: (job) => <MetricSummary metrics={job.old_metrics} /> },
            { key: 'new', label: 'New metrics', render: (job) => <MetricSummary metrics={job.new_metrics} /> },
            { key: 'job', label: 'Job', render: (job) => <span className="font-mono text-ink-secondary" title={job.id}>{job.id.slice(0, 8)}</span> },
          ]}
        />
      </TableCard>
    </>
  )
}

function MetricSummary({ metrics }) {
  const entries = Object.entries(metrics ?? {})
  if (!entries.length) return <span className="text-ink-secondary">No metrics</span>
  return (
    <span className="block max-w-56 tabular-nums text-ink">
      {entries.slice(0, 3).map(([key, value]) => `${key}: ${typeof value === 'number' ? value.toFixed(2) : value}`).join(' · ')}
    </span>
  )
}

const KIND_LABELS = { photo_alert: 'Photo check-in', sensor_alert: 'Sensor alert', password_reset: 'Temporary password', verification_code: 'Verification code' }
const kindLabel = (kind) => KIND_LABELS[kind] ?? 'Sensor alert'
const statusTone = (status) => (status?.toLowerCase() === 'sent' ? 'healthy' : status?.toLowerCase() === 'failed' ? 'critical' : 'neutral')

// 'Sent' only means the SMS service accepted the message. The phone's delivery report, when it comes, says if it arrived.
function delivery(entry) {
  if (entry.status?.toLowerCase() === 'failed') return { tone: 'critical', label: 'Not sent', note: entry.failure_reason || 'The SMS service did not accept it.' }
  if (entry.delivery_status === 'delivered') return { tone: 'healthy', label: 'Delivered' }
  if (entry.delivery_status === 'failed') return { tone: 'critical', label: 'Not delivered', note: entry.failure_reason }
  if (entry.delivery_status === 'in_transit') return { tone: 'neutral', label: 'On its way' }
  return { tone: 'neutral', label: 'No report yet' }
}

function SmsPanel() {
  const smsLog = useAdminSmsLog()
  const [statusFilter, setStatusFilter] = useState('all')
  const [farmerFilter, setFarmerFilter] = useState('all')
  const [farmFilter, setFarmFilter] = useState('all')
  const [rangeFilter, setRangeFilter] = useState('all')
  const [search, setSearch] = useState('')
  const entries = smsLog.data ?? []
  const countStatus = (status) => entries.filter((entry) => entry.status?.toLowerCase() === status).length
  const last24h = entries.filter((entry) => inDateRange(entry.created_at, '24h')).length
  const filtered = entries.filter((entry) => {
    if (statusFilter !== 'all' && entry.status?.toLowerCase() !== statusFilter) return false
    if (farmerFilter !== 'all' && entry.farmer_id !== farmerFilter) return false
    if (farmFilter !== 'all' && entry.farm_id !== farmFilter) return false
    if (!inDateRange(entry.created_at, rangeFilter)) return false
    return `${entry.farmer_name ?? ''} ${entry.farm_name ?? ''} ${entry.phone} ${entry.message}`.toLowerCase().includes(search.toLowerCase())
  })
  const farmerOptions = uniqueOptions(entries, (entry) => entry.farmer_id, (entry) => entry.farmer_name || 'Unknown farmer', 'All farmers')
  const farmOptions = uniqueOptions(entries, (entry) => entry.farm_id, (entry) => `${entry.farm_name || 'Unknown farm'} (${entry.farmer_name || 'unknown'})`, 'All farms')
  const filtersOn = search || statusFilter !== 'all' || farmerFilter !== 'all' || farmFilter !== 'all' || rangeFilter !== 'all'
  const state = { isLoading: smsLog.isLoading, isError: smsLog.isError }

  return (
    <>
      <StatStrip
        label="SMS delivery summary"
        stats={[
          { label: 'Messages sent', value: countStatus('sent'), ...state },
          { label: 'Failed to send', value: countStatus('failed'), ...state },
          { label: 'Last 24 hours', value: last24h, ...state },
        ]}
      />
      <TableCard
        id="sms-title"
        title="SMS log"
        description="This list updates every 10 seconds."
        aside={<span className="text-small tabular-nums text-ink-secondary">{filtered.length} of {entries.length} messages</span>}
        query={smsLog}
        errorText="The SMS log could not be loaded. Check your admin access and connection."
        toolbar={(
          <Toolbar>
            <SearchField label="Search SMS log" value={search} onChange={setSearch} placeholder="Search farmer, farm, phone, or message" />
            <FilterSelect id="sms-status-filter" label="Filter by status" value={statusFilter} onChange={setStatusFilter} options={[['all', 'All statuses'], ['sent', 'Sent'], ['failed', 'Failed']]} />
            <FilterSelect id="sms-farmer-filter" label="Filter by farmer" value={farmerFilter} onChange={setFarmerFilter} options={farmerOptions} />
            <FilterSelect id="sms-farm-filter" label="Filter by farm" value={farmFilter} onChange={setFarmFilter} options={farmOptions} />
            <FilterSelect id="sms-range-filter" label="Filter by date" value={rangeFilter} onChange={setRangeFilter} options={DATE_RANGES} />
          </Toolbar>
        )}
        footer="Sent means the SMS service accepted the message; Delivered appears only when the phone's delivery report reaches the server (it needs a public address and a token, so on a laptop it stays at No report yet). A message that was not accepted shows the reason, for example a wrong API key."
      >
        <DataTable
          flush
          caption="SMS log"
          rows={filtered}
          rowKey={(entry) => entry.id}
          initialSort={{ key: 'when', dir: 'desc' }}
          empty={filtersOn ? 'No messages match those filters.' : 'No text messages have been sent yet.'}
          columns={[
            { key: 'when', label: 'When', sortValue: (entry) => timeValue(entry.created_at), render: (entry) => <When value={entry.created_at} /> },
            { key: 'status', label: 'Status', sortValue: (entry) => entry.status, render: (entry) => <Tag tone={statusTone(entry.status)}><span className="capitalize">{entry.status}</span></Tag> },
            {
              key: 'delivery', label: 'Delivery', sortValue: (entry) => delivery(entry).label,
              render: (entry) => {
                const d = delivery(entry)
                return <><Tag tone={d.tone}>{d.label}</Tag>{d.note && <span className="mt-1 block max-w-56 text-caption text-ink-secondary">{d.note}</span>}</>
              },
            },
            { key: 'farmer', label: 'Farmer', sortValue: (entry) => entry.farmer_name, render: (entry) => <><span className="block font-bold text-ink">{entry.farmer_name || 'Unknown farmer'}</span><span className="block whitespace-nowrap text-caption tabular-nums text-ink-secondary">{entry.phone}</span></> },
            { key: 'farm', label: 'Farm', sortValue: (entry) => entry.farm_name, render: (entry) => <span className="text-ink">{entry.farm_name || 'Unknown farm'}</span> },
            { key: 'kind', label: 'Reason', sortValue: (entry) => entry.kind, render: (entry) => <span className="text-ink-secondary">{kindLabel(entry.kind)}{entry.severity ? `, ${entry.severity}` : ''}</span> },
            { key: 'message', label: 'Message', render: (entry) => <span className="block max-w-md text-ink">{entry.message}</span> },
          ]}
        />
      </TableCard>
    </>
  )
}
