import { Link, NavLink } from 'react-router-dom'
import { useAlerts } from '../api/hooks'
import { useFarm } from '../farm/FarmContext'
import UserMenu from './UserMenu'
import { focusRing } from './ui/styles'

// Section links show from 640px; on phones the bottom bar carries them.
const navClass = ({ isActive }) =>
  `inline-flex min-h-11 items-center gap-2 rounded-control px-3 text-small font-bold no-underline transition-colors duration-fast ${focusRing} ${
    isActive ? 'bg-brand-tint text-brand' : 'text-ink-secondary hover:bg-app-bg hover:text-ink'
  }`

// Top bar on every farmer screen: product name, section links, and the account menu.
export default function NavBar() {
  const { selectedFarmId } = useFarm()
  const { data: alerts = [] } = useAlerts(selectedFarmId)
  const unreadCount = alerts.filter((alert) => alert.status !== 'acknowledged').length

  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex min-h-16 max-w-farmer items-center justify-between gap-4 px-gutter sm:px-6">
        <Link to="/" className={`inline-flex min-h-11 items-center rounded-control text-body font-bold text-brand no-underline ${focusRing}`}>
          MaizeStressMonitor
        </Link>
        <div className="flex items-center gap-2">
          <nav aria-label="Main" className="hidden items-center gap-1 sm:flex">
            <NavLink to="/" end className={navClass}>Home</NavLink>
            <NavLink to="/check-in" className={navClass}>Check-in</NavLink>
            <NavLink to="/trends" className={navClass}>Trends</NavLink>
            <NavLink to="/alerts" className={navClass}>
              Alerts
              {unreadCount > 0 && (
                <span className="rounded-full bg-critical-text px-2 text-caption font-bold text-white">
                  {unreadCount}
                  <span className="sr-only"> unread</span>
                </span>
              )}
            </NavLink>
          </nav>
          <UserMenu profilePath="/profile" />
        </div>
      </div>
    </header>
  )
}
