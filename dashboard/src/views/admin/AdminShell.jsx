import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { focusRing } from '../../components/ui/styles'

const ICON_PATHS = {
  overview: <><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>,
  farms: <><path d="m3 10 9-7 9 7" /><path d="M5 9v12h14V9" /><path d="M9 21v-6h6v6" /></>,
  users: <><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0" /><path d="M16 4.5a3.5 3.5 0 0 1 0 7M21.5 20a6.5 6.5 0 0 0-4-6" /></>,
  feedback: <><path d="M4 5h16v11H9l-5 4z" /><path d="M8 9h8M8 12h5" /></>,
  models: <><rect x="6" y="6" width="12" height="12" rx="2" /><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4" /></>,
  retraining: <><path d="M20 12a8 8 0 1 1-2.3-5.7" /><path d="M20 4v5h-5" /></>,
  sms: <><rect x="6" y="2" width="12" height="20" rx="2" /><path d="M10 18h4" /></>,
}

const NAV_ITEMS = [
  ['overview', 'Overview'], ['farms', 'Farms'], ['users', 'Users'],
  ['feedback', 'Feedback'], ['models', 'Models'], ['retraining', 'Retraining'], ['sms', 'SMS log'],
]

function NavIcon({ section }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {ICON_PATHS[section]}
    </svg>
  )
}

function NavItem({ section, label, activeSection, onNavigate }) {
  const active = activeSection === section
  return (
    <Link
      to={section === 'overview' ? '/admin' : `/admin?view=${section}`}
      onClick={onNavigate}
      aria-current={active ? 'page' : undefined}
      className={`relative flex min-h-11 items-center gap-3 rounded-control px-3 text-small font-bold no-underline transition-colors duration-fast ${focusRing} ${active ? 'bg-brand-tint text-brand' : 'text-ink-secondary hover:bg-app-bg hover:text-ink'}`}
    >
      {active && <span aria-hidden="true" className="absolute inset-y-2 left-0 w-1 rounded-full bg-brand" />}
      <NavIcon section={section} />
      <span>{label}</span>
    </Link>
  )
}

const isWide = () => typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches

export default function AdminShell({ activeSection, children }) {
  const { name, phone, logout } = useAuth()
  const navigate = useNavigate()
  // Open beside the content on wide screens; on phones it starts closed and opens over the content.
  const [sidebarVisible, setSidebarVisible] = useState(isWide)
  const handleLogout = () => { logout(); navigate('/login', { replace: true }) }
  const closeOnNarrow = () => { if (!isWide()) setSidebarVisible(false) }

  useEffect(() => {
    if (!sidebarVisible) return
    const onKey = (event) => { if (event.key === 'Escape' && !isWide()) setSidebarVisible(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [sidebarVisible])

  return (
    <div className="min-h-screen bg-app-bg text-ink">
      <div className="flex min-h-screen">
        {sidebarVisible && (
          <>
            <button
              type="button"
              aria-label="Close menu"
              onClick={() => setSidebarVisible(false)}
              className="fixed inset-0 z-20 min-h-0 rounded-none bg-ink/40 lg:hidden"
            />
            <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-border bg-surface shadow-raised lg:sticky lg:top-0 lg:h-screen lg:shadow-none">
              <Link to="/admin" onClick={closeOnNarrow} className={`flex items-baseline gap-2 px-5 pb-4 pt-6 text-ink no-underline ${focusRing}`}>
                <span className="text-heading">Maize Monitor</span>
                <span className="text-caption font-bold text-ink-secondary">Admin</span>
              </Link>
              <nav aria-label="Admin sections" className="flex flex-1 flex-col gap-1 overflow-y-auto px-3 py-2">
                {NAV_ITEMS.map(([section, label]) => (
                  <NavItem key={section} section={section} label={label} activeSection={activeSection} onNavigate={closeOnNarrow} />
                ))}
              </nav>
              <div className="border-t border-border p-4">
                <p className="m-0 truncate text-small font-bold">{name || 'Administrator'}</p>
                {phone && <p className="m-0 truncate text-caption text-ink-secondary">{phone}</p>}
                <button type="button" onClick={handleLogout} className={`mt-3 min-h-11 w-full rounded-control border-[1.5px] border-control bg-surface px-3 text-left text-small font-bold text-ink hover:bg-app-bg ${focusRing}`}>
                  Log out
                </button>
              </div>
            </aside>
          </>
        )}
        <div className="min-w-0 flex-1">
          <div className="sticky top-0 z-10 flex min-h-14 items-center justify-between gap-3 border-b border-border bg-surface px-4 sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <button
                type="button"
                onClick={() => setSidebarVisible((visible) => !visible)}
                aria-label={sidebarVisible ? 'Hide menu' : 'Show menu'}
                aria-expanded={sidebarVisible}
                className={`flex h-11 w-11 min-h-11 items-center justify-center rounded-control border-[1.5px] border-control bg-surface text-ink hover:bg-app-bg ${focusRing}`}
              >
                <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  {sidebarVisible ? <path d="M15 6l-6 6 6 6" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
                </svg>
              </button>
              <span className="truncate text-small text-ink-secondary">
                Admin <span aria-hidden="true" className="mx-1">/</span> <span className="font-bold text-ink">{NAV_ITEMS.find(([key]) => key === activeSection)?.[1]}</span>
              </span>
            </div>
            {!sidebarVisible && (
              <button type="button" onClick={handleLogout} className={`min-h-11 rounded-control border-[1.5px] border-control bg-surface px-3 text-small font-bold text-ink hover:bg-app-bg ${focusRing}`}>
                Log out
              </button>
            )}
          </div>
          <main id="main-content" className="mx-auto w-full max-w-[1440px] p-4 sm:p-6 lg:p-8">{children}</main>
        </div>
      </div>
    </div>
  )
}
