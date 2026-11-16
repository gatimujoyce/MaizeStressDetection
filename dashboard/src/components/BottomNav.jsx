import { NavLink } from 'react-router-dom'
import { BellIcon, CameraIcon, ChartIcon, HomeIcon } from './NavIcons'
import { useAlerts } from '../api/hooks'
import { useFarm } from '../farm/FarmContext'

const navItems = [
  { label: 'Home', to: '/', icon: HomeIcon, end: true },
  { label: 'Check-in', to: '/check-in', icon: CameraIcon },
  { label: 'Trends', to: '/trends', icon: ChartIcon },
  { label: 'Alerts', to: '/alerts', icon: BellIcon },
]

// Section links on phones. The current section is marked by colour, weight and a bar above it.
export default function BottomNav() {
  const { selectedFarmId } = useFarm()
  const { data: alerts = [] } = useAlerts(selectedFarmId)
  const unreadCount = alerts.filter((alert) => alert.status !== 'acknowledged').length

  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-surface pb-[env(safe-area-inset-bottom,0px)] sm:hidden"
    >
      <div className="flex w-full items-stretch">
        {navItems.map(({ label, to, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `relative flex min-h-16 flex-1 flex-col items-center justify-center gap-1 py-2 text-small no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-focus ${
                isActive ? 'font-bold text-brand' : 'text-ink-secondary'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && <span aria-hidden="true" className="absolute inset-x-4 top-0 h-1 rounded-full bg-brand" />}
                <span className="relative">
                  <Icon className="h-6 w-6" />
                  {label === 'Alerts' && unreadCount > 0 && (
                    <span className="absolute -right-2 -top-2 flex h-5 min-w-5 items-center justify-center rounded-full bg-critical-text px-1 text-caption font-bold text-white">
                      {unreadCount}
                      <span className="sr-only"> unread</span>
                    </span>
                  )}
                </span>
                <span>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
