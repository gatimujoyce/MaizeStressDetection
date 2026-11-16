import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAdminAuditLog } from '../../api/adminManage'
import { useAuth } from '../../auth/AuthContext'
import ChangePasswordDialog from '../../components/ChangePasswordDialog'
import useNameRow from '../../components/useNameRow'
import Card, { SectionHeader } from '../../components/ui/Card'
import DataTable from '../../components/ui/DataTable'
import DescriptionList from '../../components/ui/DescriptionList'
import Notice from '../../components/ui/Notice'
import Skeleton from '../../components/ui/Skeleton'
import { buttonClass, linkClass } from '../../components/ui/styles'
import { actionLabel } from '../../content/auditLabels'
import { formatDateTime } from '../../content/dates'
import { ChangeList } from './ManagePanels'

const RECENT = 10
const ROLE_NAMES = { farmer: 'Farmer', admin: 'Administrator' }

// The signed-in administrator's last few entries in the activity log, matched by id (two admins can share a name).
function RecentActions({ userId }) {
  const log = useAdminAuditLog()
  const mine = (log.data ?? [])
    .filter((entry) => entry.admin_id && entry.admin_id === userId)
    .sort((a, b) => (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0))
    .slice(0, RECENT)

  return (
    <section aria-labelledby="recent-actions-title">
      <SectionHeader
        id="recent-actions-title"
        title="Your recent actions"
        description={`The last ${RECENT} changes you made, from the activity log.`}
        aside={<Link to="/admin?view=audit" className={`inline-flex min-h-11 items-center text-small ${linkClass}`}>Full activity log</Link>}
      />
      {log.isLoading ? (
        <Skeleton label="Loading your recent actions" className="h-24" />
      ) : log.isError ? (
        <Notice tone="critical" onRetry={() => log.refetch()} retrying={log.isFetching}>
          <p>Your recent actions could not be loaded.</p>
        </Notice>
      ) : (
        <DataTable
          caption="Your recent actions"
          rows={mine}
          rowKey={(entry) => entry.id}
          maxHeight=""
          empty="You have not changed anything yet. Edits to farmers, farms and sensor keys appear here."
          columns={[
            { key: 'when', label: 'When', render: (entry) => <span className="whitespace-nowrap tabular-nums text-ink-secondary">{formatDateTime(entry.created_at)}</span> },
            { key: 'action', label: 'Action', render: (entry) => <span className="text-ink">{actionLabel(entry.action)}</span> },
            { key: 'target', label: 'Who or what', render: (entry) => <span className="text-ink">{entry.target_label}</span> },
            { key: 'changes', label: 'What changed', render: (entry) => <ChangeList entry={entry} /> },
          ]}
        />
      )}
    </section>
  )
}

export default function AdminProfile() {
  const { name, phone, role, userId, logout, refreshProfile } = useAuth()
  const navigate = useNavigate()
  const [changingPassword, setChangingPassword] = useState(false)
  const nameRow = useNameRow(name, refreshProfile)

  const signOut = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <>
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
                    <span className="block text-small text-ink-secondary">Your phone number cannot be changed here.</span>
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

        <RecentActions userId={userId} />

        <div>
          <button type="button" onClick={signOut} className={buttonClass({ variant: 'secondary' })}>
            Sign out
          </button>
        </div>
      </Card>
      {changingPassword && <ChangePasswordDialog onClose={() => setChangingPassword(false)} />}
    </>
  )
}
