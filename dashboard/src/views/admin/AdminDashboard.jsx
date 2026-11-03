import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAdminFarms, useAdminFeedback, useAdminModelVersions, useAdminRetrainingJobs, useAdminSmsLog, useAdminUsers, useCreateAdminUserMutation, useRequestAdminRetrainMutation, useSetAdminModelVersionActiveMutation } from '../../api/hooks'
import Badge from '../../components/ui/Badge'
import Card, { SectionHeader } from '../../components/ui/Card'
import DataTable from '../../components/ui/DataTable'
import Notice from '../../components/ui/Notice'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import StatTile from '../../components/ui/StatTile'
import Toolbar, { FilterSelect, SearchField } from '../../components/ui/Toolbar'
import { buttonClass, focusRing, insetClass, linkClass } from '../../components/ui/styles'
import { DATE_RANGES, inDateRange, uniqueOptions } from '../../components/ui/adminFilters'
import AdminShell from './AdminShell'
import { AuditPanel, FarmEditor, UserEditor } from './ManagePanels'

const SECTIONS = {
  overview: {
    title: 'Overview',
    description: 'A live snapshot of farms, users, and SMS alert records.',
  },
  farms: {
    title: 'Farm monitoring',
    description: 'Review registered farms and their latest field status.',
  },
  users: {
    title: 'Users',
    description: 'Review farmer and administrator accounts.',
  },
  feedback: {
    title: 'Feedback',
    description: 'Review farmer responses to prediction results.',
  },
  models: {
    title: 'Model versions',
    description: 'Review model versions and active deployments.',
  },
  retraining: {
    title: 'Retraining',
    description: 'Review retraining history and request a run.',
  },
  sms: {
    title: 'SMS log',
    description: 'Review SMS alert delivery records.',
  },
  audit: {
    title: 'Activity log',
    description: 'A permanent record of what administrators changed, and when.',
  },
}

const adminFieldClass = `mt-1 block min-h-11 w-full rounded-control border-[1.5px] border-control bg-surface px-3 text-small font-normal text-ink ${focusRing}`

function CountBadge({ children, tone = 'neutral' }) {
  return <Badge tone={tone} size="sm" icon={false}>{children}</Badge>
}

function LoadingRows() {
  return (
    <div className="flex flex-col gap-2">
      <Skeleton label="Loading" className="h-11" />
      <Skeleton className="h-11" />
      <Skeleton className="h-11" />
    </div>
  )
}

const timeValue = (value) => (value ? Date.parse(value) || null : null)

export default function AdminDashboard() {
  const [searchParams] = useSearchParams()
  const requestedSection = searchParams.get('view')
  const activeSection = Object.hasOwn(SECTIONS, requestedSection) ? requestedSection : 'overview'
  const section = SECTIONS[activeSection]

  return (
    <AdminShell activeSection={activeSection}>
      <div className="mb-6">
        <PageHeader title={section.title} subtitle={section.description} />
      </div>

      {activeSection === 'overview'
        ? <AdminOverview />
        : activeSection === 'users'
          ? <UsersPanel />
        : activeSection === 'farms'
          ? <FarmsPanel />
        : activeSection === 'feedback'
          ? <FeedbackPanel />
        : activeSection === 'models'
          ? <ModelsPanel />
        : activeSection === 'retraining'
          ? <RetrainingPanel />
        : activeSection === 'sms'
          ? <SmsPanel />
        : activeSection === 'audit'
          ? <AuditPanel />
        : <ComingSoonPanel title={section.title} />}
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

  return (
    <div className="flex flex-col gap-6">
      {(farms.isError || users.isError || smsLog.isError) && (
        <Notice tone="critical">
          <p>Some overview data could not be loaded. Check your connection or access, then refresh.</p>
        </Notice>
      )}

      <section aria-label="Admin overview counts" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile label="Registered farms" value={farms.data?.length ?? 0} isLoading={farms.isLoading} isError={farms.isError} />
        <StatTile
          label="User accounts"
          value={userRows.length}
          isLoading={users.isLoading}
          isError={users.isError}
          detail={`${farmerCount} ${farmerCount === 1 ? 'farmer' : 'farmers'} · ${adminCount} ${adminCount === 1 ? 'admin' : 'admins'}`}
        />
        <StatTile
          label="SMS alert records"
          value={smsRows.length}
          isLoading={smsLog.isLoading}
          isError={smsLog.isError}
          detail={`${smsCount('sent')} sent · ${smsCount('failed')} failed · ${smsCount('pending')} pending`}
        />
      </section>

      <Card aria-labelledby="recent-farms-title">
        <SectionHeader
          id="recent-farms-title"
          title="Registered farms"
          aside={<span className="text-small text-ink-secondary">{farms.data?.length ?? 0} total</span>}
        />
        {farms.isLoading ? (
          <LoadingRows />
        ) : farms.data?.length ? (
          <>
            <ul className="m-0 list-none divide-y divide-border p-0">
              {farms.data.slice(0, 5).map((farm) => (
                <li key={farm.id} className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 py-3 first:pt-0">
                  <span className="text-small font-bold text-ink">{farm.name}</span>
                  <span className="text-small text-ink-secondary">
                    {[farm.location, farm.soil_type?.replaceAll('_', ' ')].filter(Boolean).join(' · ')}
                  </span>
                </li>
              ))}
            </ul>
            {farms.data.length > 5 && (
              <Link to="/admin?view=farms" className={`mt-2 inline-flex min-h-11 items-center text-small ${linkClass}`}>
                All {farms.data.length} farms →
              </Link>
            )}
          </>
        ) : (
          <p className="m-0 text-small text-ink-secondary">
            {farms.isError ? 'Farm records are unavailable.' : 'No farms have been registered yet.'}
          </p>
        )}
      </Card>
    </div>
  )
}

function ComingSoonPanel({ title }) {
  return (
    <Card>
      <p className="m-0 text-small text-ink-secondary">
        The {title.toLowerCase()} panel will be connected in its implementation task.
      </p>
    </Card>
  )
}

function UsersPanel() {
  const users = useAdminUsers()
  const createAdmin = useCreateAdminUserMutation()
  const [form, setForm] = useState({ name: '', phone: '', password: '' })
  const [search, setSearch] = useState('')
  const [createdName, setCreatedName] = useState('')
  const [managedId, setManagedId] = useState(null)
  const managed = (users.data ?? []).find((user) => user.id === managedId)
  const filteredUsers = (users.data ?? []).filter((user) => `${user.name} ${user.phone} ${user.role}`.toLowerCase().includes(search.toLowerCase()))

  async function handleSubmit(event) {
    event.preventDefault()
    setCreatedName('')
    try {
      const result = await createAdmin.mutateAsync(form)
      setCreatedName(result.name)
      setForm({ name: '', phone: '', password: '' })
    } catch { /* Mutation state displays the API error below. */ }
  }

  return (
    <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(300px,.8fr)]">
      <Card aria-labelledby="users-title">
        <SectionHeader id="users-title" title="People with access" aside={<CountBadge>{users.data?.length ?? 0} accounts</CountBadge>} />
        <Toolbar>
          <SearchField label="Search users" value={search} onChange={setSearch} placeholder="Search name, phone, or role" />
        </Toolbar>
        {users.isError && <Notice tone="critical" className="mb-4"><p>Could not load users. Check your admin access and connection.</p></Notice>}
        {users.isLoading ? <LoadingRows /> : (
          <DataTable
            caption="User accounts"
            rows={filteredUsers}
            rowKey={(user) => user.id}
            initialSort={{ key: 'name', dir: 'asc' }}
            empty={search ? 'No accounts match this search.' : 'No accounts found.'}
            columns={[
              { key: 'name', label: 'Name', sortValue: (user) => user.name, render: (user) => <span className="font-bold text-ink">{user.name}</span> },
              { key: 'phone', label: 'Phone', sortValue: (user) => user.phone, render: (user) => <span className="tabular-nums text-ink-secondary">{user.phone}</span> },
              { key: 'role', label: 'Role', sortValue: (user) => user.role, render: (user) => <CountBadge tone={user.role === 'admin' ? 'healthy' : 'neutral'}><span className="capitalize">{user.role}</span></CountBadge> },
              {
                key: 'manage', label: '',
                render: (user) => user.role === 'farmer'
                  ? <button type="button" onClick={() => setManagedId(user.id)} className={buttonClass({ variant: 'secondary', size: 'sm' })}>Manage</button>
                  : null,
              },
            ]}
          />
        )}
      </Card>

      <Card aria-labelledby="add-admin-title">
        <SectionHeader id="add-admin-title" title="Add an administrator" />
        <p className="mb-4 mt-0 text-small text-ink-secondary">Create a separate admin login for a trusted team member.</p>
        {createdName && <Notice tone="positive" className="mb-4"><p>Administrator account created for {createdName}.</p></Notice>}
        {createAdmin.isError && <Notice tone="critical" className="mb-4"><p>{createAdmin.error?.message || 'Could not create the administrator. Check whether the phone is already registered.'}</p></Notice>}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="text-small font-bold">Full name<input required autoComplete="name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className={adminFieldClass} /></label>
          <label className="text-small font-bold">Kenyan phone number<input required type="tel" autoComplete="tel" placeholder="07… or +254…" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} className={adminFieldClass} /></label>
          <label className="text-small font-bold">Temporary password<input required minLength={8} type="password" autoComplete="new-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} className={adminFieldClass} /></label>
          <button disabled={createAdmin.isPending} type="submit" className={`mt-1 ${buttonClass({ size: 'sm' })}`}>{createAdmin.isPending ? 'Creating account…' : 'Create admin account'}</button>
        </form>
      </Card>
      {managed && <div className="xl:col-span-2"><UserEditor key={managed.id} user={managed} onClose={() => setManagedId(null)} /></div>}
    </div>
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
    <Card aria-labelledby="farms-title">
      <SectionHeader id="farms-title" title="Registered farms" aside={<CountBadge>{farms.data?.length ?? 0} {includeDeleted ? 'records' : 'active farms'}</CountBadge>} />
      <Toolbar>
        <SearchField label="Search farms" value={search} onChange={setSearch} placeholder="Search farm, farmer, location, crop, or soil" />
        <label className="flex min-h-11 cursor-pointer items-center gap-2 rounded-control border-[1.5px] border-control bg-surface px-3 text-small font-bold text-ink">
          <input type="checkbox" checked={includeDeleted} onChange={(event) => setIncludeDeleted(event.target.checked)} className="h-4 w-4 min-h-0 accent-brand" />
          Include archived farms
        </label>
        <button type="button" onClick={() => setEditing('new')} className={buttonClass({ size: 'sm' })}>Add a farm</button>
      </Toolbar>
      {editing && (
        <div className="mb-4">
          <FarmEditor key={editing === 'new' ? 'new' : editing.id} farm={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />
        </div>
      )}
      {farms.isError && <Notice tone="critical" className="mb-4"><p>Farm records could not be loaded. Check your admin access and connection.</p></Notice>}
      {farms.isLoading ? <LoadingRows /> : (
        <DataTable
          caption="Registered farms"
          rows={visibleFarms}
          rowKey={(farm) => farm.id}
          initialSort={{ key: 'name', dir: 'asc' }}
          empty={search ? 'No farms match this search.' : 'No farm records found.'}
          columns={[
            {
              key: 'name', label: 'Farm', sortValue: (farm) => farm.name,
              render: (farm) => <><span className="block font-bold text-ink">{farm.name}</span><span className="mt-0.5 block text-caption text-ink-secondary">{farm.size_acres ? `${farm.size_acres} acres` : 'Size not set'}</span></>,
            },
            {
              key: 'owner', label: 'Farmer', sortValue: (farm) => farm.owner_name,
              render: (farm) => <><span className="block font-bold text-ink">{farm.owner_name || 'Unknown farmer'}</span><span className="mt-0.5 block text-caption tabular-nums text-ink-secondary">{farm.owner_phone}</span></>,
            },
            { key: 'location', label: 'Location', sortValue: (farm) => farm.location, render: (farm) => <span className="text-ink-secondary">{farm.location}</span> },
            {
              key: 'land', label: 'Land', sortValue: (farm) => farm.soil_type,
              render: (farm) => <><span className="capitalize text-ink">{farm.soil_type?.replaceAll('_', ' ') || 'Not recorded'}</span>{farm.planting_date && <span className="mt-0.5 block text-caption text-ink-secondary">Planted {farm.planting_date}</span>}</>,
            },
            { key: 'crop', label: 'Crop details', sortValue: (farm) => farm.seed_variety, render: (farm) => <span className="text-ink-secondary">{farm.seed_variety || 'Not recorded'}</span> },
            { key: 'water', label: 'Water source', sortValue: (farm) => farm.water_source, render: (farm) => <span className="text-ink-secondary">{farm.water_source || 'Not recorded'}</span> },
            {
              key: 'status', label: 'Status', sortValue: (farm) => (farm.deleted_at ? 'Archived' : 'Active'),
              render: (farm) => (farm.deleted_at ? <CountBadge>Archived</CountBadge> : <CountBadge tone="healthy">Active</CountBadge>),
            },
            {
              key: 'npk', label: 'NPK sensor', sortValue: (farm) => (farm.has_npk_sensor ? 1 : 0),
              render: (farm) => (farm.has_npk_sensor ? <CountBadge tone="healthy">On</CountBadge> : <span className="text-ink-secondary">Off</span>),
            },
            {
              key: 'edit', label: '',
              render: (farm) => <button type="button" onClick={() => setEditing(farm)} className={buttonClass({ variant: 'secondary', size: 'sm' })}>Edit</button>,
            },
          ]}
        />
      )}
      <p className="mb-0 mt-3 text-caption text-ink-secondary">Showing {visibleFarms.length} of {farms.data?.length ?? 0} returned records.</p>
    </Card>
  )
}

function FeedbackPanel() {
  const feedback = useAdminFeedback()
  const [filter, setFilter] = useState('all')
  const [farmFilter, setFarmFilter] = useState('all')
  const [search, setSearch] = useState('')
  const rows = feedback.data ?? []
  const farmOptions = uniqueOptions(rows, (item) => item.farm_id, (item) => `${item.farm_name} (${item.farmer_name})`, 'All farms')
  const inaccurateCount = rows.filter((item) => !item.accurate).length
  const filtered = rows.filter((item) => {
    if (filter === 'inaccurate' && item.accurate) return false
    if (filter === 'useful' && item.useful !== true) return false
    if (farmFilter !== 'all' && item.farm_id !== farmFilter) return false
    return `${item.correct_label ?? ''} ${item.comment ?? ''} ${item.farm_name ?? ''} ${item.farmer_name ?? ''} ${item.disease_label ?? ''}`.toLowerCase().includes(search.toLowerCase())
  })

  return (
    <div className="flex flex-col gap-6">
      <section aria-label="Feedback summary" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile label="Responses received" value={rows.length} isLoading={feedback.isLoading} isError={feedback.isError} />
        <StatTile label="Marked inaccurate" value={inaccurateCount} isLoading={feedback.isLoading} isError={feedback.isError} />
        <StatTile label="Marked useful" value={rows.filter((item) => item.useful === true).length} isLoading={feedback.isLoading} isError={feedback.isError} />
      </section>
      <Card aria-labelledby="feedback-title">
        <SectionHeader id="feedback-title" title="Prediction feedback" aside={<CountBadge tone={inaccurateCount ? 'warning' : 'neutral'}>{inaccurateCount} flagged inaccurate</CountBadge>} />
        <Toolbar>
          <SearchField label="Search feedback" value={search} onChange={setSearch} placeholder="Search farm, farmer, comment, or result" />
          <FilterSelect id="feedback-filter" label="Filter feedback" value={filter} onChange={setFilter} options={[['all', 'All feedback'], ['inaccurate', 'Marked inaccurate'], ['useful', 'Marked useful']]} />
          <FilterSelect id="feedback-farm-filter" label="Filter by farm" value={farmFilter} onChange={setFarmFilter} options={farmOptions} />
        </Toolbar>
        {feedback.isError && <Notice tone="critical" className="mb-4"><p>Feedback could not be loaded. Check your admin access and connection.</p></Notice>}
        {feedback.isLoading ? <LoadingRows /> : filtered.length ? (
          <ul className="m-0 flex list-none flex-col divide-y divide-border p-0">
            {filtered.map((item) => (
              <li key={item.id} className="py-4 first:pt-0 last:pb-0">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap gap-2">
                    <CountBadge tone={item.accurate ? 'healthy' : 'critical'}>{item.accurate ? 'Prediction accurate' : 'Marked inaccurate'}</CountBadge>
                    {item.useful != null && <CountBadge>{item.useful ? 'Useful' : 'Not useful'}</CountBadge>}
                  </div>
                  <time className="text-caption text-ink-secondary" dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time>
                </div>
                {item.correct_label && <p className="mb-0 mt-2 text-small"><span className="font-bold">Suggested label:</span> {item.correct_label}</p>}
                {item.comment && <blockquote className="mx-0 mb-0 mt-2 border-l-2 border-control pl-3 text-small text-ink-secondary">{item.comment}</blockquote>}
                <p className="mb-0 mt-2 text-caption text-ink-secondary">{item.farmer_name} / {item.farm_name}{item.disease_label ? ` / result: ${item.disease_label.replaceAll('_', ' ')}` : ''}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="m-0 rounded-control bg-app-bg p-5 text-center text-small text-ink-secondary">{search || filter !== 'all' ? 'No feedback matches those filters.' : 'No farmer feedback has been submitted yet.'}</p>
        )}
      </Card>
    </div>
  )
}

function ModelsPanel() {
  const versions = useAdminModelVersions()
  const setActive = useSetAdminModelVersionActiveMutation()
  const [search, setSearch] = useState('')
  const records = versions.data ?? []
  const modelNames = [...new Set(records.map((item) => item.model_name))]
  const filtered = records.filter((item) => `${item.model_name} ${item.version} ${Object.keys(item.metrics ?? {}).join(' ')}`.toLowerCase().includes(search.toLowerCase()))
  const activeTotal = records.filter((item) => item.is_active).length
  const formatMetric = (value) => typeof value === 'number' ? (value <= 1 ? `${(value * 100).toFixed(1)}%` : value.toFixed(2)) : String(value)

  return (
    <div className="flex flex-col gap-6">
      <section aria-label="Model version summary" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile label="Model families" value={modelNames.length} isLoading={versions.isLoading} isError={versions.isError} />
        <StatTile label="Registered versions" value={records.length} isLoading={versions.isLoading} isError={versions.isError} />
        <StatTile label="Active deployments" value={activeTotal} isLoading={versions.isLoading} isError={versions.isError} />
      </section>
      <Card aria-labelledby="models-title">
        <SectionHeader id="models-title" title="Model versions" aside={<CountBadge tone="healthy">{activeTotal} active</CountBadge>} />
        <Toolbar>
          <SearchField label="Search model versions" value={search} onChange={setSearch} placeholder="Search model, version, or metric" />
        </Toolbar>
        {versions.isError && <Notice tone="critical" className="mb-4"><p>Model versions could not be loaded. Check your admin access and connection.</p></Notice>}
        {setActive.isError && <Notice tone="critical" className="mb-4"><p>{setActive.error?.message || 'The deployment status could not be updated.'}</p></Notice>}
        {versions.isLoading ? <LoadingRows /> : filtered.length ? (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {filtered.map((item) => (
              <article key={item.id} className={`flex flex-col rounded-card border p-4 sm:p-5 ${item.is_active ? 'border-2 border-brand' : 'border-border'}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="m-0 text-caption font-bold text-ink-secondary">{item.model_name} model</p>
                    <h3 className="mb-0 mt-0.5 text-title">{item.version}</h3>
                  </div>
                  {item.is_active ? <CountBadge tone="healthy">Active</CountBadge> : <CountBadge>Standby</CountBadge>}
                </div>
                {Object.entries(item.metrics ?? {}).length ? (
                  <dl className="my-4 grid grid-cols-2 gap-2">
                    {Object.entries(item.metrics).map(([key, value]) => (
                      <div key={key} className={insetClass}>
                        <dt className="truncate text-caption capitalize text-ink-secondary">{key.replaceAll('_', ' ')}</dt>
                        <dd className="mb-0 mt-0.5 truncate text-small font-bold tabular-nums text-ink">{formatMetric(value)}</dd>
                      </div>
                    ))}
                  </dl>
                ) : <p className="my-4 text-small text-ink-secondary">No evaluation metrics recorded.</p>}
                <button
                  type="button"
                  disabled={item.is_active || setActive.isPending}
                  onClick={() => setActive.mutate({ versionId: item.id, isActive: true })}
                  className={`mt-auto ${buttonClass({ variant: 'secondary', size: 'sm', block: true })}`}
                >
                  {item.is_active ? 'Currently deployed' : setActive.isPending ? 'Updating deployment…' : 'Set as active version'}
                </button>
              </article>
            ))}
          </div>
        ) : (
          <p className="m-0 rounded-control bg-app-bg p-5 text-center text-small text-ink-secondary">{search ? 'No model versions match this search.' : 'No model versions have been registered yet.'}</p>
        )}
        {modelNames.length > 1 && <p className="mb-0 mt-3 text-caption text-ink-secondary">Activating a version replaces the active version for that model family.</p>}
      </Card>
    </div>
  )
}

function RetrainingPanel() {
  const [modelName, setModelName] = useState('triage')
  const jobs = useAdminRetrainingJobs()
  const requestRun = useRequestAdminRetrainMutation()
  const [requestResult, setRequestResult] = useState(null)
  const sortedJobs = [...(jobs.data ?? [])].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  const deployed = sortedJobs.filter((job) => job.deployed).length
  const passed = sortedJobs.filter((job) => job.passed_gate).length

  async function handleRequest(event) {
    event.preventDefault()
    setRequestResult(null)
    try {
      setRequestResult(await requestRun.mutateAsync(modelName))
    } catch { /* Mutation error appears below the form. */ }
  }

  return (
    <div className="flex flex-col gap-6">
      <section aria-label="Retraining summary" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile label="Recorded runs" value={sortedJobs.length} isLoading={jobs.isLoading} isError={jobs.isError} />
        <StatTile label="Passed quality gate" value={passed} isLoading={jobs.isLoading} isError={jobs.isError} />
        <StatTile label="Deployed outcomes" value={deployed} isLoading={jobs.isLoading} isError={jobs.isError} />
      </section>

      <section className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(280px,.7fr)_minmax(0,1.6fr)]">
        <Card aria-labelledby="request-title">
          <SectionHeader id="request-title" title="Request retraining" />
          <p className="mb-4 mt-0 text-small text-ink-secondary">Choose a model family to submit a retraining request.</p>
          {requestResult && (
            <Notice tone="positive" title="Request accepted" className="mb-4">
              <p>{requestResult.model_name} · {requestResult.status} · Job ID {requestResult.job_id}</p>
            </Notice>
          )}
          {requestRun.isError && <Notice tone="critical" className="mb-4"><p>{requestRun.error?.message || 'The retraining request could not be submitted.'}</p></Notice>}
          <form onSubmit={handleRequest} className="flex flex-col gap-4">
            <label className="text-small font-bold">Model family
              <select value={modelName} onChange={(event) => setModelName(event.target.value)} className={adminFieldClass}>
                <option value="triage">Triage</option><option value="disease">Disease</option><option value="nutrient">Nutrient</option><option value="sensor">Sensor</option>
              </select>
            </label>
            <button type="submit" disabled={requestRun.isPending} className={buttonClass({ size: 'sm' })}>{requestRun.isPending ? 'Submitting request…' : 'Request retraining'}</button>
          </form>
          <p className="mb-0 mt-4 text-caption text-ink-secondary">The server response confirms receipt of the request. Job history below shows records returned by the backend.</p>
        </Card>

        <Card aria-labelledby="history-title">
          <SectionHeader id="history-title" title="Quality and deployment" aside={<span className="text-caption text-ink-secondary">{passed} passed · {deployed} deployed</span>} />
          {jobs.isError && <Notice tone="critical" className="mb-4"><p>Retraining history could not be loaded. Check your admin access and connection.</p></Notice>}
          {jobs.isLoading ? <LoadingRows /> : (
            <DataTable
              caption="Retraining run history"
              rows={sortedJobs}
              rowKey={(job) => job.id}
              initialSort={{ key: 'created', dir: 'desc' }}
              empty="No retraining history has been recorded yet."
              columns={[
                { key: 'model', label: 'Model', sortValue: (job) => job.model_name, render: (job) => <span className="font-bold capitalize text-ink">{job.model_name}</span> },
                { key: 'created', label: 'Requested', sortValue: (job) => timeValue(job.created_at), render: (job) => <span className="text-ink-secondary">{new Date(job.created_at).toLocaleString()}</span> },
                { key: 'gate', label: 'Quality gate', sortValue: (job) => (job.passed_gate ? 1 : 0), render: (job) => <CountBadge tone={job.passed_gate ? 'healthy' : 'critical'}>{job.passed_gate ? 'Quality gate passed' : 'Quality gate failed'}</CountBadge> },
                { key: 'deployed', label: 'Deployed', sortValue: (job) => (job.deployed ? 1 : 0), render: (job) => <span className="text-ink-secondary">{job.deployed ? 'Deployed' : 'Not deployed'}</span> },
                { key: 'old', label: 'Previous metrics', render: (job) => <MetricSummary metrics={job.old_metrics} /> },
                { key: 'new', label: 'New metrics', render: (job) => <MetricSummary metrics={job.new_metrics} /> },
                { key: 'job', label: 'Job', render: (job) => <span className="font-mono text-caption text-ink-secondary" title={job.id}>{job.id.slice(0, 8)}</span> },
              ]}
            />
          )}
        </Card>
      </section>
    </div>
  )
}

function MetricSummary({ metrics }) {
  const entries = Object.entries(metrics ?? {})
  if (!entries.length) return <span className="text-caption text-ink-secondary">No metrics</span>
  return (
    <span className="block max-w-56 text-caption tabular-nums text-ink">
      {entries.slice(0, 3).map(([key, value]) => `${key}: ${typeof value === 'number' ? value.toFixed(2) : value}`).join(' · ')}
    </span>
  )
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
  const statusTone = (status) => (status?.toLowerCase() === 'sent' ? 'healthy' : status?.toLowerCase() === 'failed' ? 'critical' : 'neutral')
  const kindLabel = (kind) => (kind === 'photo_alert' ? 'Photo check-in' : 'Sensor alert')
  const filtersOn = search || statusFilter !== 'all' || farmerFilter !== 'all' || farmFilter !== 'all' || rangeFilter !== 'all'

  return (
    <div className="flex flex-col gap-6">
      <section aria-label="SMS delivery summary" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile label="Messages sent" value={countStatus('sent')} isLoading={smsLog.isLoading} isError={smsLog.isError} />
        <StatTile label="Failed to send" value={countStatus('failed')} isLoading={smsLog.isLoading} isError={smsLog.isError} />
        <StatTile label="Last 24 hours" value={last24h} isLoading={smsLog.isLoading} isError={smsLog.isError} />
      </section>
      <Card aria-labelledby="sms-title">
        <SectionHeader id="sms-title" title="SMS log" aside={<CountBadge>{filtered.length} of {entries.length} messages</CountBadge>} />
        <Toolbar>
          <SearchField label="Search SMS log" value={search} onChange={setSearch} placeholder="Search farmer, farm, phone, or message" />
          <FilterSelect id="sms-status-filter" label="Filter by status" value={statusFilter} onChange={setStatusFilter} options={[['all', 'All statuses'], ['sent', 'Sent'], ['failed', 'Failed']]} />
        </Toolbar>
        <Toolbar>
          <FilterSelect id="sms-farmer-filter" label="Filter by farmer" value={farmerFilter} onChange={setFarmerFilter} options={farmerOptions} />
          <FilterSelect id="sms-farm-filter" label="Filter by farm" value={farmFilter} onChange={setFarmFilter} options={farmOptions} />
          <FilterSelect id="sms-range-filter" label="Filter by date" value={rangeFilter} onChange={setRangeFilter} options={DATE_RANGES} />
        </Toolbar>
        {smsLog.isError && <Notice tone="critical" className="mb-4"><p>The SMS log could not be loaded. Check your admin access and connection.</p></Notice>}
        {smsLog.isLoading ? <LoadingRows /> : (
          <DataTable
            caption="SMS log"
            rows={filtered}
            rowKey={(entry) => entry.id}
            initialSort={{ key: 'when', dir: 'desc' }}
            empty={filtersOn ? 'No messages match those filters.' : 'No text messages have been sent yet.'}
            columns={[
              { key: 'when', label: 'When', sortValue: (entry) => timeValue(entry.created_at), render: (entry) => <span className="whitespace-nowrap text-ink-secondary">{new Date(entry.created_at).toLocaleString()}</span> },
              { key: 'status', label: 'Status', sortValue: (entry) => entry.status, render: (entry) => <CountBadge tone={statusTone(entry.status)}><span className="capitalize">{entry.status}</span></CountBadge> },
              { key: 'farmer', label: 'Farmer', sortValue: (entry) => entry.farmer_name, render: (entry) => <><span className="block font-bold text-ink">{entry.farmer_name || 'Unknown farmer'}</span><span className="mt-0.5 block text-caption tabular-nums text-ink-secondary">{entry.phone}</span></> },
              { key: 'farm', label: 'Farm', sortValue: (entry) => entry.farm_name, render: (entry) => <span className="text-ink">{entry.farm_name || 'Unknown farm'}</span> },
              { key: 'kind', label: 'Reason', sortValue: (entry) => entry.kind, render: (entry) => <span className="text-ink-secondary">{kindLabel(entry.kind)}{entry.severity ? `, ${entry.severity}` : ''}</span> },
              { key: 'message', label: 'Message', render: (entry) => <span className="block max-w-md text-small text-ink">{entry.message}</span> },
            ]}
          />
        )}
        <p className="mb-0 mt-3 text-caption text-ink-secondary">
          This list updates every 10 seconds. A message shows as Failed when the SMS service did not accept it, for example when the API key is missing or wrong.
        </p>
      </Card>
    </div>
  )
}
