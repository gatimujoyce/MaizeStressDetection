import { NavLink } from 'react-router-dom'
import { BellIcon, CameraIcon, ChartIcon, HomeIcon } from './NavIcons'

const navItems = [
  { label: 'Home', to: '/', icon: HomeIcon, end: true },
  { label: 'Check-in', to: '/check-in', icon: CameraIcon },
  { label: 'Trends', to: '/trends', icon: ChartIcon },
  { label: 'Alerts', to: '/alerts', icon: BellIcon },
]

export default function BottomNav() {
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-[var(--color-border)] bg-[var(--color-surface)] pb-0 sm:hidden"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
    >
      <div className="flex w-full items-stretch">
        {navItems.map(({ label, to, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex min-h-16 flex-1 flex-col items-center justify-center gap-1 rounded-sm py-2 text-xs font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-brand)] focus-visible:ring-inset ${
                isActive ? 'text-[var(--color-brand)]' : 'text-[var(--color-text-secondary)]'
              }`
            }
          >
            {label === 'Check-in' ? (
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-brand)] text-white">
                <Icon className="h-6 w-6" />
              </span>
            ) : (
              <Icon className="h-6 w-6" />
            )}
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
