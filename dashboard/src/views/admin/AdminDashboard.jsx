import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAdminFarms, useAdminFeedback, useAdminModelVersions, useAdminRetrainingJobs, useAdminSmsLog, useAdminUsers, useCreateAdminUserMutation, useRequestAdminRetrainMutation, useSetAdminModelVersionActiveMutation } from '../../api/hooks'
import AdminShell from './AdminShell'

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
}

export default function AdminDashboard() {
  const [searchParams] = useSearchParams()
  const requestedSection = searchParams.get('view')
  const activeSection = Object.hasOwn(SECTIONS, requestedSection) ? requestedSection : 'overview'
  const section = SECTIONS[activeSection]

  return (
    <AdminShell activeSection={activeSection}>
      <header className="relative mb-7 overflow-hidden rounded-3xl bg-gradient-to-br from-brand to-emerald-800 px-6 py-7 text-white shadow-xl shadow-brand/15 sm:px-8 sm:py-9">
        <div aria-hidden="true" className="pointer-events-none absolute -right-10 -top-24 h-72 w-72 rounded-full border-[36px] border-white/10" />
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-28 right-28 h-56 w-56 rounded-full bg-lime-300/10 blur-2xl" />
        <div className="relative">
          <p className="mb-2 text-xs font-bold uppercase tracking-[.18em] text-white/70">Admin workspace</p>
          <h1 className="m-0 text-3xl font-extrabold sm:text-4xl">{section.title}</h1>
          <p className="mt-2 max-w-2xl text-base text-white/80">{section.description}</p>
        </div>
      </header>

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
        : <ComingSoonPanel title={section.title} />}
    </AdminShell>
  )
}

function AdminOverview() {
  const farms = useAdminFarms()
  const users = useAdminUsers()
  const smsLog = useAdminSmsLog()

  return (
    <div className="flex flex-col gap-6">
      {(farms.isError || users.isError || smsLog.isError) && (
        <div role="alert" className="rounded-xl border border-critical-text/30 bg-critical-bg p-4 text-sm text-critical-text">
          Some overview data could not be loaded. Check your connection or access, then refresh.
        </div>
      )}

      <section aria-label="Admin overview counts" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <OverviewCard label="Registered farms" query={farms} />
        <OverviewCard label="User accounts" query={users} />
        <OverviewCard label="SMS alert records" query={smsLog} />
      </section>

      <section aria-labelledby="recent-farms-title" className="rounded-2xl border border-border bg-surface p-4 sm:p-6">
        <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="recent-farms-title" className="m-0 text-xl font-bold text-ink">Registered farms</h2>
          <span className="text-sm text-ink-secondary">{farms.data?.length ?? 0} total</span>
        </div>

        {farms.isLoading ? (
          <p className="m-0 text-sm text-ink-secondary">Loading farms…</p>
        ) : farms.data?.length ? (
          <ul className="m-0 divide-y divide-border p-0">
            {farms.data.slice(0, 5).map((farm) => (
              <li key={farm.id} className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 py-3 first:pt-0 last:pb-0">
                <span className="font-semibold text-ink">{farm.name}</span>
                <span className="text-sm text-ink-secondary">
                  {[farm.location, farm.soil_type?.replaceAll('_', ' ')].filter(Boolean).join(' · ')}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="m-0 text-sm text-ink-secondary">
            {farms.isError ? 'Farm records are unavailable.' : 'No farms have been registered yet.'}
          </p>
        )}
      </section>
    </div>
  )
}

function OverviewCard({ label, query }) {
  const value = query.isLoading ? '…' : query.isError ? 'Unavailable' : (query.data?.length ?? 0)
  return (
    <article className="rounded-2xl border border-border bg-surface p-5">
      <p className="m-0 text-sm font-semibold text-ink-secondary">{label}</p>
      <p className="mb-0 mt-2 text-3xl font-bold tabular-nums text-ink">{value}</p>
    </article>
  )
}

function ComingSoonPanel({ title }) {
  return (
    <section className="rounded-2xl border border-border bg-surface p-5 sm:p-6">
      <p className="m-0 text-base text-ink-secondary">
        The {title.toLowerCase()} panel will be connected in its implementation task.
      </p>
    </section>
  )
}

function UsersPanel() {
  const users = useAdminUsers()
  const createAdmin = useCreateAdminUserMutation()
  const [form, setForm] = useState({ name: '', phone: '', password: '' })
  const [search, setSearch] = useState('')
  const [createdName, setCreatedName] = useState('')
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
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(300px,.8fr)]">
      <section className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-7">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div><p className="m-0 text-xs font-bold uppercase tracking-widest text-brand">Directory</p><h2 className="mb-0 mt-1 text-xl font-extrabold">People with access</h2></div>
          <span className="rounded-full bg-brand-tint px-3 py-1 text-sm font-bold text-brand">{users.data?.length ?? 0} accounts</span>
        </div>
        <label className="mb-4 block"><span className="sr-only">Search users</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name, phone, or role" className="w-full rounded-xl border border-border bg-app-bg px-4 py-3 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" /></label>
        {users.isError && <p role="alert" className="rounded-xl bg-critical-bg p-3 text-sm text-critical-text">Could not load users. Check your admin access and connection.</p>}
        {users.isLoading ? <p className="text-sm text-ink-secondary">Loading account directory…</p> : filteredUsers.length ? <ul className="m-0 divide-y divide-border p-0">{filteredUsers.map((user) => <li key={user.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-tint font-bold text-brand">{user.name.slice(0, 1).toUpperCase()}</span><span className="min-w-0 flex-1"><span className="block truncate font-bold">{user.name}</span><span className="block text-sm text-ink-secondary">{user.phone}</span></span><span className={`rounded-full px-3 py-1 text-xs font-bold capitalize ${user.role === 'admin' ? 'bg-brand-tint text-brand' : 'bg-neutral-bg text-ink-secondary'}`}>{user.role}</span></li>)}</ul> : <p className="rounded-xl bg-app-bg p-4 text-sm text-ink-secondary">{search ? 'No accounts match this search.' : 'No accounts found.'}</p>}
      </section>

      <section className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-7">
        <div className="mb-5"><p className="m-0 text-xs font-bold uppercase tracking-widest text-brand">Access management</p><h2 className="mb-0 mt-1 text-xl font-extrabold">Add an administrator</h2><p className="mb-0 mt-2 text-sm leading-5 text-ink-secondary">Create a separate admin login for a trusted team member.</p></div>
        {createdName && <p role="status" className="mb-4 rounded-xl bg-positive-bg p-3 text-sm font-semibold text-positive-text">Administrator account created for {createdName}.</p>}
        {createAdmin.isError && <p role="alert" className="mb-4 rounded-xl bg-critical-bg p-3 text-sm text-critical-text">{createAdmin.error?.message || 'Could not create the administrator. Check whether the phone is already registered.'}</p>}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="text-sm font-semibold">Full name<input required autoComplete="name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className="mt-1 block w-full rounded-xl border border-border bg-app-bg px-3 py-3 font-normal outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" /></label>
          <label className="text-sm font-semibold">Kenyan phone number<input required type="tel" autoComplete="tel" placeholder="07… or +254…" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} className="mt-1 block w-full rounded-xl border border-border bg-app-bg px-3 py-3 font-normal outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" /></label>
          <label className="text-sm font-semibold">Temporary password<input required minLength={8} type="password" autoComplete="new-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} className="mt-1 block w-full rounded-xl border border-border bg-app-bg px-3 py-3 font-normal outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" /></label>
          <button disabled={createAdmin.isPending} type="submit" className="mt-1 min-h-12 rounded-xl bg-brand px-4 py-3 text-sm font-bold text-white shadow-md shadow-brand/20 transition hover:bg-brand/90 disabled:cursor-wait disabled:opacity-60">{createAdmin.isPending ? 'Creating account…' : 'Create admin account'}</button>
        </form>
      </section>
    </div>
  )
}

function FarmsPanel() {
  const [includeDeleted, setIncludeDeleted] = useState(false)
  const [search, setSearch] = useState('')
  const farms = useAdminFarms(includeDeleted)
  const visibleFarms = (farms.data ?? []).filter((farm) => {
    const fields = [farm.name, farm.location, farm.soil_type, farm.seed_variety, farm.water_source]
    return fields.filter(Boolean).join(' ').toLowerCase().includes(search.toLowerCase())
  })

  return (
    <section className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-7">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div><p className="m-0 text-xs font-bold uppercase tracking-widest text-brand">Field directory</p><h2 className="mb-0 mt-1 text-xl font-extrabold">Registered farms</h2></div>
        <span className="rounded-full bg-brand-tint px-3 py-1 text-sm font-bold text-brand">{farms.data?.length ?? 0} {includeDeleted ? 'records' : 'active farms'}</span>
      </div>
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <label className="min-w-0 flex-1"><span className="sr-only">Search farms</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search farm, location, crop, or soil" className="w-full rounded-xl border border-border bg-app-bg px-4 py-3 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" /></label>
        <label className="flex min-h-11 items-center gap-2 rounded-xl border border-border px-3 text-sm font-semibold text-ink-secondary"><input type="checkbox" checked={includeDeleted} onChange={(event) => setIncludeDeleted(event.target.checked)} className="h-4 w-4 accent-brand" />Include archived farms</label>
      </div>
      {farms.isError && <p role="alert" className="rounded-xl bg-critical-bg p-4 text-sm text-critical-text">Farm records could not be loaded. Check your admin access and connection.</p>}
      {farms.isLoading ? <p className="py-8 text-center text-sm text-ink-secondary">Loading farm records…</p> : visibleFarms.length ? (
        <div className="overflow-x-auto rounded-2xl border border-border">
          <table className="w-full min-w-[780px] border-collapse text-left text-sm">
            <thead className="bg-app-bg text-xs uppercase tracking-wide text-ink-secondary"><tr><th className="px-4 py-3 font-bold">Farm</th><th className="px-4 py-3 font-bold">Location</th><th className="px-4 py-3 font-bold">Land</th><th className="px-4 py-3 font-bold">Crop details</th><th className="px-4 py-3 font-bold">Water source</th><th className="px-4 py-3 font-bold">Status</th></tr></thead>
            <tbody className="divide-y divide-border">{visibleFarms.map((farm) => <tr key={farm.id} className="hover:bg-app-bg/70">
              <td className="px-4 py-4"><span className="block font-bold text-ink">{farm.name}</span><span className="mt-1 block text-xs text-ink-secondary">{farm.size_acres ? `${farm.size_acres} acres` : 'Size not set'}</span></td>
              <td className="px-4 py-4 text-ink-secondary">{farm.location}</td>
              <td className="px-4 py-4"><span className="capitalize text-ink">{farm.soil_type?.replaceAll('_', ' ') || 'Not recorded'}</span>{farm.planting_date && <span className="mt-1 block text-xs text-ink-secondary">Planted {farm.planting_date}</span>}</td>
              <td className="px-4 py-4 text-ink-secondary">{farm.seed_variety || 'Not recorded'}</td>
              <td className="px-4 py-4 text-ink-secondary">{farm.water_source || 'Not recorded'}</td>
              <td className="px-4 py-4">{farm.deleted_at ? <span className="rounded-full bg-neutral-bg px-3 py-1 text-xs font-bold text-ink-secondary">Archived</span> : <span className="rounded-full bg-positive-bg px-3 py-1 text-xs font-bold text-positive-text">Active</span>}</td>
            </tr>)}</tbody>
          </table>
        </div>
      ) : <p className="rounded-xl bg-app-bg p-5 text-center text-sm text-ink-secondary">{search ? 'No farms match this search.' : 'No farm records found.'}</p>}
      <p className="mb-0 mt-4 text-xs text-ink-secondary">Showing {visibleFarms.length} of {farms.data?.length ?? 0} returned records.</p>
    </section>
  )
}

function FeedbackPanel() {
  const feedback = useAdminFeedback()
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const rows = feedback.data ?? []
  const inaccurateCount = rows.filter((item) => !item.accurate).length
  const filtered = rows.filter((item) => {
    if (filter === 'inaccurate' && item.accurate) return false
    if (filter === 'useful' && item.useful !== true) return false
    return `${item.correct_label ?? ''} ${item.comment ?? ''} ${item.prediction_id}`.toLowerCase().includes(search.toLowerCase())
  })

  return (
    <div className="flex flex-col gap-5">
      <section aria-label="Feedback summary" className="grid gap-4 sm:grid-cols-3">
        <OverviewCard label="Responses received" query={{ isLoading: feedback.isLoading, isError: feedback.isError, data: rows }} />
        <OverviewCard label="Marked inaccurate" query={{ isLoading: feedback.isLoading, isError: feedback.isError, data: rows.filter((item) => !item.accurate) }} />
        <OverviewCard label="Marked useful" query={{ isLoading: feedback.isLoading, isError: feedback.isError, data: rows.filter((item) => item.useful === true) }} />
      </section>
      <section className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-7">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div><p className="m-0 text-xs font-bold uppercase tracking-widest text-brand">Farmer voice</p><h2 className="mb-0 mt-1 text-xl font-extrabold">Prediction feedback</h2></div>
          <span className="rounded-full bg-brand-tint px-3 py-1 text-sm font-bold text-brand">{inaccurateCount} flagged inaccurate</span>
        </div>
        <div className="mb-5 flex flex-col gap-3 sm:flex-row">
          <label className="min-w-0 flex-1"><span className="sr-only">Search feedback</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search comments, labels, or prediction ID" className="w-full rounded-xl border border-border bg-app-bg px-4 py-3 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" /></label>
          <label className="sr-only" htmlFor="feedback-filter">Filter feedback</label><select id="feedback-filter" value={filter} onChange={(event) => setFilter(event.target.value)} className="min-h-11 rounded-xl border border-border bg-surface px-3 text-sm font-semibold outline-none focus:border-brand"><option value="all">All feedback</option><option value="inaccurate">Marked inaccurate</option><option value="useful">Marked useful</option></select>
        </div>
        {feedback.isError && <p role="alert" className="rounded-xl bg-critical-bg p-4 text-sm text-critical-text">Feedback could not be loaded. Check your admin access and connection.</p>}
        {feedback.isLoading ? <p className="py-8 text-center text-sm text-ink-secondary">Loading feedback…</p> : filtered.length ? <ul className="m-0 flex flex-col gap-3 p-0">{filtered.map((item) => <li key={item.id} className="rounded-2xl border border-border bg-app-bg/70 p-4 sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap gap-2"><span className={`rounded-full px-3 py-1 text-xs font-bold ${item.accurate ? 'bg-positive-bg text-positive-text' : 'bg-critical-bg text-critical-text'}`}>{item.accurate ? 'Prediction accurate' : 'Marked inaccurate'}</span>{item.useful != null && <span className="rounded-full bg-surface px-3 py-1 text-xs font-semibold text-ink-secondary">{item.useful ? 'Useful' : 'Not useful'}</span>}</div>
            <time className="text-xs text-ink-secondary" dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time>
          </div>
          {item.correct_label && <p className="mb-0 mt-3 text-sm"><span className="font-bold">Suggested label:</span> {item.correct_label}</p>}
          {item.comment && <blockquote className="mb-0 mt-3 border-l-2 border-brand/40 pl-3 text-sm leading-6 text-ink-secondary">{item.comment}</blockquote>}
          <p className="mb-0 mt-3 truncate text-xs text-ink-secondary">Prediction ID: {item.prediction_id}</p>
        </li>)}</ul> : <p className="rounded-xl bg-app-bg p-5 text-center text-sm text-ink-secondary">{search || filter !== 'all' ? 'No feedback matches those filters.' : 'No farmer feedback has been submitted yet.'}</p>}
      </section>
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
    <div className="flex flex-col gap-5">
      <section aria-label="Model version summary" className="grid gap-4 sm:grid-cols-3">
        <OverviewCard label="Model families" query={{ isLoading: versions.isLoading, isError: versions.isError, data: modelNames }} />
        <OverviewCard label="Registered versions" query={{ isLoading: versions.isLoading, isError: versions.isError, data: records }} />
        <OverviewCard label="Active deployments" query={{ isLoading: versions.isLoading, isError: versions.isError, data: records.filter((item) => item.is_active) }} />
      </section>
      <section className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-7">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div><p className="m-0 text-xs font-bold uppercase tracking-widest text-brand">Deployment registry</p><h2 className="mb-0 mt-1 text-xl font-extrabold">Model versions</h2></div>
          <span className="rounded-full bg-positive-bg px-3 py-1 text-sm font-bold text-positive-text">{activeTotal} active</span>
        </div>
        <label className="mb-5 block"><span className="sr-only">Search model versions</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search model, version, or metric" className="w-full rounded-xl border border-border bg-app-bg px-4 py-3 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" /></label>
        {versions.isError && <p role="alert" className="rounded-xl bg-critical-bg p-4 text-sm text-critical-text">Model versions could not be loaded. Check your admin access and connection.</p>}
        {setActive.isError && <p role="alert" className="mb-4 rounded-xl bg-critical-bg p-4 text-sm text-critical-text">{setActive.error?.message || 'The deployment status could not be updated.'}</p>}
        {versions.isLoading ? <p className="py-8 text-center text-sm text-ink-secondary">Loading model versions…</p> : filtered.length ? <div className="grid gap-4 lg:grid-cols-2">{filtered.map((item) => <article key={item.id} className={`rounded-2xl border p-5 ${item.is_active ? 'border-brand/40 bg-brand-tint/30' : 'border-border bg-app-bg/60'}`}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div><p className="m-0 text-xs font-bold uppercase tracking-widest text-ink-secondary">{item.model_name} model</p><h3 className="mb-0 mt-1 text-xl font-extrabold">{item.version}</h3></div>
            <span className={`rounded-full px-3 py-1 text-xs font-bold ${item.is_active ? 'bg-positive-bg text-positive-text' : 'bg-surface text-ink-secondary'}`}>{item.is_active ? 'Active' : 'Standby'}</span>
          </div>
          {Object.entries(item.metrics ?? {}).length ? <dl className="my-5 grid grid-cols-2 gap-2">{Object.entries(item.metrics).map(([key, value]) => <div key={key} className="rounded-xl bg-surface/80 p-3"><dt className="truncate text-xs capitalize text-ink-secondary">{key.replaceAll('_', ' ')}</dt><dd className="mb-0 mt-1 truncate text-sm font-bold text-ink">{formatMetric(value)}</dd></div>)}</dl> : <p className="my-5 text-sm text-ink-secondary">No evaluation metrics recorded.</p>}
          <button type="button" disabled={item.is_active || setActive.isPending} onClick={() => setActive.mutate({ versionId: item.id, isActive: true })} className="min-h-10 w-full rounded-xl border border-brand px-4 py-2 text-sm font-bold text-brand transition hover:bg-brand hover:text-white disabled:cursor-not-allowed disabled:border-border disabled:bg-surface disabled:text-ink-secondary">{item.is_active ? 'Currently deployed' : setActive.isPending ? 'Updating deployment…' : 'Set as active version'}</button>
        </article>)}</div> : <p className="rounded-xl bg-app-bg p-5 text-center text-sm text-ink-secondary">{search ? 'No model versions match this search.' : 'No model versions have been registered yet.'}</p>}
        {modelNames.length > 1 && <p className="mb-0 mt-4 text-xs text-ink-secondary">Activating a version replaces the active version for that model family.</p>}
      </section>
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
    <div className="flex flex-col gap-5">
      <section aria-label="Retraining summary" className="grid gap-4 sm:grid-cols-3">
        <OverviewCard label="Recorded runs" query={{ isLoading: jobs.isLoading, isError: jobs.isError, data: sortedJobs }} />
        <OverviewCard label="Passed quality gate" query={{ isLoading: jobs.isLoading, isError: jobs.isError, data: sortedJobs.filter((job) => job.passed_gate) }} />
        <OverviewCard label="Deployed outcomes" query={{ isLoading: jobs.isLoading, isError: jobs.isError, data: sortedJobs.filter((job) => job.deployed) }} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(300px,.75fr)_minmax(0,1.4fr)]">
        <div className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-7">
          <p className="m-0 text-xs font-bold uppercase tracking-widest text-brand">Model operations</p><h2 className="mb-0 mt-1 text-xl font-extrabold">Request retraining</h2>
          <p className="mb-5 mt-2 text-sm leading-5 text-ink-secondary">Choose a model family to submit a retraining request.</p>
          {requestResult && <div role="status" className="mb-4 rounded-xl bg-positive-bg p-4 text-sm text-positive-text"><p className="m-0 font-bold">Request accepted</p><p className="mb-0 mt-1">{requestResult.model_name} · {requestResult.status} · Job ID {requestResult.job_id}</p></div>}
          {requestRun.isError && <p role="alert" className="rounded-xl bg-critical-bg p-4 text-sm text-critical-text">{requestRun.error?.message || 'The retraining request could not be submitted.'}</p>}
          <form onSubmit={handleRequest} className="flex flex-col gap-4">
            <label className="text-sm font-semibold">Model family<select value={modelName} onChange={(event) => setModelName(event.target.value)} className="mt-1 block min-h-12 w-full rounded-xl border border-border bg-app-bg px-3 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"><option value="triage">Triage</option><option value="disease">Disease</option><option value="nutrient">Nutrient</option><option value="sensor">Sensor</option></select></label>
            <button type="submit" disabled={requestRun.isPending} className="min-h-12 rounded-xl bg-brand px-4 py-3 text-sm font-bold text-white shadow-md shadow-brand/20 transition hover:bg-brand/90 disabled:cursor-wait disabled:opacity-60">{requestRun.isPending ? 'Submitting request…' : 'Request retraining'}</button>
          </form>
          <p className="mb-0 mt-4 text-xs leading-5 text-ink-secondary">The server response confirms receipt of the request. Job history below shows records returned by the backend.</p>
        </div>

        <section className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-7">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><p className="m-0 text-xs font-bold uppercase tracking-widest text-brand">Run history</p><h2 className="mb-0 mt-1 text-xl font-extrabold">Quality and deployment</h2></div><span className="text-xs text-ink-secondary">{passed} passed · {deployed} deployed</span></div>
          {jobs.isError && <p role="alert" className="rounded-xl bg-critical-bg p-4 text-sm text-critical-text">Retraining history could not be loaded. Check your admin access and connection.</p>}
          {jobs.isLoading ? <p className="py-8 text-center text-sm text-ink-secondary">Loading run history…</p> : sortedJobs.length ? <ul className="m-0 flex flex-col gap-3 p-0">{sortedJobs.map((job) => <li key={job.id} className="rounded-2xl border border-border bg-app-bg/60 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2"><div><p className="m-0 text-xs font-bold uppercase tracking-widest text-ink-secondary">{job.model_name}</p><p className="mb-0 mt-1 text-sm font-semibold">{new Date(job.created_at).toLocaleString()}</p></div><span className={`rounded-full px-3 py-1 text-xs font-bold ${job.passed_gate ? 'bg-positive-bg text-positive-text' : 'bg-critical-bg text-critical-text'}`}>{job.passed_gate ? 'Quality gate passed' : 'Quality gate failed'}</span></div>
            <div className="mt-3 flex flex-wrap gap-2"><span className="rounded-full bg-surface px-3 py-1 text-xs font-semibold text-ink-secondary">{job.deployed ? 'Deployed' : 'Not deployed'}</span><span className="rounded-full bg-surface px-3 py-1 text-xs font-semibold text-ink-secondary">Job {job.id.slice(0, 8)}</span></div>
            <div className="mt-3 grid grid-cols-2 gap-3"><MetricSummary title="Previous metrics" metrics={job.old_metrics} /><MetricSummary title="New metrics" metrics={job.new_metrics} /></div>
          </li>)}</ul> : <p className="rounded-xl bg-app-bg p-5 text-center text-sm text-ink-secondary">No retraining history has been recorded yet.</p>}
        </section>
      </section>
    </div>
  )
}

function MetricSummary({ title, metrics }) {
  const entries = Object.entries(metrics ?? {})
  return <div className="rounded-xl bg-surface p-3"><p className="m-0 text-xs font-bold text-ink-secondary">{title}</p>{entries.length ? <p className="mb-0 mt-1 truncate text-xs text-ink">{entries.slice(0, 3).map(([key, value]) => `${key}: ${typeof value === 'number' ? value.toFixed(2) : value}`).join(' · ')}</p> : <p className="mb-0 mt-1 text-xs text-ink-secondary">No metrics</p>}</div>
}

function SmsPanel() {
  const smsLog = useAdminSmsLog()
  const [statusFilter, setStatusFilter] = useState('all')
  const [search, setSearch] = useState('')
  const entries = smsLog.data ?? []
  const sentCount = entries.filter((entry) => entry.status?.toLowerCase() === 'sent').length
  const failedCount = entries.filter((entry) => entry.status?.toLowerCase() === 'failed').length
  const pendingCount = entries.filter((entry) => entry.status?.toLowerCase() === 'pending').length
  const filtered = entries.filter((entry) => {
    if (statusFilter !== 'all' && entry.status?.toLowerCase() !== statusFilter) return false
    return `${entry.severity} ${entry.status} ${entry.farm_id} ${entry.prediction_id} ${entry.id}`.toLowerCase().includes(search.toLowerCase())
  }).sort((a, b) => new Date(b.sent_at ?? 0) - new Date(a.sent_at ?? 0))

  return (
    <div className="flex flex-col gap-5">
      <section aria-label="SMS delivery summary" className="grid gap-4 sm:grid-cols-3">
        <OverviewCard label="Messages sent" query={{ isLoading: smsLog.isLoading, isError: smsLog.isError, data: entries.filter((entry) => entry.status?.toLowerCase() === 'sent') }} />
        <OverviewCard label="Delivery failed" query={{ isLoading: smsLog.isLoading, isError: smsLog.isError, data: entries.filter((entry) => entry.status?.toLowerCase() === 'failed') }} />
        <OverviewCard label="Awaiting delivery" query={{ isLoading: smsLog.isLoading, isError: smsLog.isError, data: entries.filter((entry) => entry.status?.toLowerCase() === 'pending') }} />
      </section>
      <section className="rounded-3xl border border-border bg-surface p-5 shadow-sm sm:p-7">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><p className="m-0 text-xs font-bold uppercase tracking-widest text-brand">Communications</p><h2 className="mb-0 mt-1 text-xl font-extrabold">SMS delivery log</h2></div><span className="rounded-full bg-brand-tint px-3 py-1 text-sm font-bold text-brand">{entries.length} records</span></div>
        <div className="mb-5 flex flex-col gap-3 sm:flex-row">
          <label className="min-w-0 flex-1"><span className="sr-only">Search SMS log</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search farm, prediction, severity, or ID" className="w-full rounded-xl border border-border bg-app-bg px-4 py-3 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20" /></label>
          <label className="sr-only" htmlFor="sms-status-filter">Filter SMS status</label><select id="sms-status-filter" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="min-h-11 rounded-xl border border-border bg-surface px-3 text-sm font-semibold outline-none focus:border-brand"><option value="all">All statuses</option><option value="sent">Sent</option><option value="failed">Failed</option><option value="pending">Pending</option></select>
        </div>
        {smsLog.isError && <p role="alert" className="rounded-xl bg-critical-bg p-4 text-sm text-critical-text">SMS records could not be loaded. Check your admin access and connection.</p>}
        {smsLog.isLoading ? <p className="py-8 text-center text-sm text-ink-secondary">Loading SMS records…</p> : filtered.length ? <div className="overflow-x-auto rounded-2xl border border-border"><table className="w-full min-w-[760px] border-collapse text-left text-sm">
          <thead className="bg-app-bg text-xs uppercase tracking-wide text-ink-secondary"><tr><th className="px-4 py-3 font-bold">Status</th><th className="px-4 py-3 font-bold">Severity</th><th className="px-4 py-3 font-bold">Farm</th><th className="px-4 py-3 font-bold">Prediction</th><th className="px-4 py-3 font-bold">Sent at</th><th className="px-4 py-3 font-bold">Alert ID</th></tr></thead>
          <tbody className="divide-y divide-border">{filtered.map((entry) => <tr key={entry.id} className="hover:bg-app-bg/70">
            <td className="px-4 py-4"><span className={`rounded-full px-3 py-1 text-xs font-bold capitalize ${entry.status?.toLowerCase() === 'sent' ? 'bg-positive-bg text-positive-text' : entry.status?.toLowerCase() === 'failed' ? 'bg-critical-bg text-critical-text' : 'bg-neutral-bg text-ink-secondary'}`}>{entry.status}</span></td>
            <td className="px-4 py-4 font-semibold">{entry.severity}</td><td className="max-w-40 truncate px-4 py-4 font-mono text-xs text-ink-secondary" title={entry.farm_id}>{entry.farm_id}</td><td className="max-w-40 truncate px-4 py-4 font-mono text-xs text-ink-secondary" title={entry.prediction_id}>{entry.prediction_id}</td>
            <td className="px-4 py-4 text-ink-secondary">{entry.sent_at ? new Date(entry.sent_at).toLocaleString() : '—'}</td><td className="max-w-40 truncate px-4 py-4 font-mono text-xs text-ink-secondary" title={entry.id}>{entry.id}</td>
          </tr>)}</tbody>
        </table></div> : <p className="rounded-xl bg-app-bg p-5 text-center text-sm text-ink-secondary">{search || statusFilter !== 'all' ? 'No SMS records match those filters.' : 'No SMS alerts have been recorded yet.'}</p>}
        {pendingCount + failedCount + sentCount < entries.length && <p className="mb-0 mt-4 text-xs text-ink-secondary">Some records use statuses outside the sent, failed, or pending categories.</p>}
      </section>
    </div>
  )
}
