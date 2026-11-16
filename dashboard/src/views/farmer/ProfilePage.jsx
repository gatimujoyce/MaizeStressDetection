import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useGrowthStage, useUpdateProfileMutation } from '../../api/hooks'
import { useAuth } from '../../auth/AuthContext'
import ChangePasswordDialog from '../../components/ChangePasswordDialog'
import Card, { SectionHeader } from '../../components/ui/Card'
import DescriptionList from '../../components/ui/DescriptionList'
import EmptyState from '../../components/ui/EmptyState'
import Notice from '../../components/ui/Notice'
import Page from '../../components/ui/Page'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { buttonClass, fieldClass, focusRing, labelClass, linkClass } from '../../components/ui/styles'
import { formatDay } from '../../content/dates'
import { useFarm } from '../../farm/FarmContext'

const NAME_MIN = 2
const NAME_MAX = 60

const SENSOR_STATUS = {
  installed: 'Sensor installed',
  requested: 'Sensor requested',
  in_progress: 'Visit being arranged',
  none: 'Photo checks only',
}

const ROLE_NAMES = { farmer: 'Farmer', admin: 'Administrator' }

// The Name row of the account list, with an Edit button that turns it into a field.
// Same rules as the server: trimmed, 2 to 60 characters.
function useNameRow(name, onSaved) {
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

function PlotStage({ farmId }) {
  const { data: stage, isLoading } = useGrowthStage(farmId)
  if (isLoading) return <span className="text-ink-secondary">Loading…</span>
  if (!stage?.known) return <span className="text-ink-secondary">Not known</span>
  return stage.label
}

// On phones each plot is a block of label and value lines; from 640px it is an ordinary table row.
const cellClass = 'flex justify-between gap-4 py-1 text-small before:font-bold before:text-ink-secondary before:content-[attr(data-label)] sm:table-cell sm:py-3 sm:pr-4 sm:before:content-none'

function MyPlots() {
  const { farms, isLoading, isError, retryFarms, selectFarm } = useFarm()
  const navigate = useNavigate()

  const open = (farmId) => {
    selectFarm(farmId)
    navigate('/')
  }

  return (
    <section aria-labelledby="plots-title">
      <SectionHeader
        id="plots-title"
        title="My plots"
        aside={<Link to="/plots/new" className={`inline-flex min-h-11 items-center text-small ${linkClass}`}>Add a plot</Link>}
      />
      {isLoading ? (
        <Skeleton label="Loading your plots" className="h-24" />
      ) : isError ? (
        <Notice tone="critical" onRetry={() => retryFarms()}>
          <p>Could not load your plots.</p>
        </Notice>
      ) : farms.length === 0 ? (
        <EmptyState action={<Link to="/plots/new" className={buttonClass({ size: 'sm' })}>Add a plot</Link>}>
          <p>You have no plots yet.</p>
        </EmptyState>
      ) : (
        <table className="block w-full border-collapse text-left sm:table">
          <caption className="sr-only">Your plots</caption>
          <thead className="sr-only sm:not-sr-only sm:table-header-group">
            <tr className="border-b border-border">
              {['Plot', 'Growth stage', 'Sensor', 'Planted'].map((heading) => (
                <th key={heading} scope="col" className="pb-2 pr-4 text-small font-bold text-ink-secondary">{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody className="block divide-y divide-border sm:table-row-group">
            {farms.map((farm) => (
              <tr key={farm.farm_id} className="block py-3 first:pt-0 sm:table-row">
                <th scope="row" className="block pb-1 text-left font-normal sm:table-cell sm:py-3 sm:pr-4">
                  <button
                    type="button"
                    onClick={() => open(farm.farm_id)}
                    className={`min-h-11 cursor-pointer bg-transparent px-0 text-left text-body font-bold text-brand underline underline-offset-4 ${focusRing}`}
                  >
                    {farm.farm_name}
                  </button>
                </th>
                <td data-label="Growth stage" className={cellClass}><PlotStage farmId={farm.farm_id} /></td>
                <td data-label="Sensor" className={cellClass}>{SENSOR_STATUS[farm.sensor_status || 'none'] ?? SENSOR_STATUS.none}</td>
                <td data-label="Planted" className={`${cellClass} sm:whitespace-nowrap`}>
                  {formatDay(farm.plantingDate) || 'Not planted yet'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

export default function ProfilePage() {
  const { name, phone, role, logout, refreshProfile } = useAuth()
  const navigate = useNavigate()
  const [changingPassword, setChangingPassword] = useState(false)
  const nameRow = useNameRow(name, refreshProfile)

  const signOut = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <Page>
      <PageHeader title="Profile" subtitle={name || undefined} />

      <Card divided>
        <section aria-labelledby="account-title">
          <SectionHeader id="account-title" title="Account" />
          <DescriptionList
            items={[
              nameRow,
              {
                label: 'Phone number',
                value: (
                  <>
                    <span className="tabular-nums">{phone || 'Not set'}</span>
                    <span className="block text-small text-ink-secondary">To change your number, contact your administrator.</span>
                  </>
                ),
              },
              { label: 'Role', value: ROLE_NAMES[role] ?? role ?? '' },
            ]}
          />
        </section>

        <section aria-labelledby="security-title">
          <SectionHeader id="security-title" title="Security" />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="m-0 text-body text-ink">Password</p>
            <button type="button" onClick={() => setChangingPassword(true)} className={buttonClass({ variant: 'secondary', size: 'sm' })}>
              Change password
            </button>
          </div>
        </section>

        <MyPlots />

        <section aria-labelledby="sms-title">
          <SectionHeader id="sms-title" title="Alerts by SMS" />
          <p className="m-0 text-body text-ink">
            Alerts are sent by SMS to <span className="font-bold tabular-nums">{phone || 'your phone number'}</span>.
          </p>
        </section>

        <div>
          <button type="button" onClick={signOut} className={buttonClass({ variant: 'secondary' })}>
            Sign out
          </button>
        </div>
      </Card>

      {changingPassword && <ChangePasswordDialog onClose={() => setChangingPassword(false)} />}
    </Page>
  )
}
