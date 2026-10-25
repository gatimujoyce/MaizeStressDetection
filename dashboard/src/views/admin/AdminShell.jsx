import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'

const NAV_ITEMS = [
  ['overview', 'Overview', '◫'], ['farms', 'Farms', '⌂'], ['users', 'Users', '♙'],
  ['feedback', 'Feedback', '✳'], ['models', 'Models', '◉'], ['retraining', 'Retraining', '↻'], ['sms', 'SMS log', '▤'],
]

function NavItem({ section, label, icon, activeSection, onNavigate }) {
  const active = activeSection === section
  return (
    <Link
      to={section === 'overview' ? '/admin' : `/admin?view=${section}`}
      onClick={onNavigate}
      aria-current={active ? 'page' : undefined}
      className={`group relative flex min-h-12 items-center gap-3 overflow-hidden rounded-xl px-3 text-left text-sm font-semibold transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand ${active ? 'bg-brand text-white shadow-md shadow-brand/20' : 'text-ink-secondary hover:bg-neutral-bg hover:text-ink'}`}
    >
      <span aria-hidden="true" className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-lg ${active ? 'bg-white/15 text-white' : 'bg-neutral-bg text-brand group-hover:bg-white'}`}>{icon}</span>
      <span>{label}</span>
    </Link>
  )
}

export default function AdminShell({ activeSection, children }) {
  const { name, phone, logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarVisible, setSidebarVisible] = useState(true)
  const handleLogout = () => { logout(); navigate('/login', { replace: true }) }

  return (
    <div className="min-h-screen bg-app-bg text-ink">
      <div className="flex min-h-screen">
        {sidebarVisible && <aside className="fixed inset-y-0 left-0 z-30 flex w-[278px] flex-col border-r border-border bg-surface shadow-xl shadow-ink/5 lg:sticky lg:top-0 lg:h-screen lg:shadow-none">
          <Link to="/admin" className="flex items-center gap-3 px-5 py-6 text-ink no-underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-brand to-emerald-700 text-lg font-black text-white shadow-lg shadow-brand/25">M</span>
            <span><span className="block text-base font-extrabold leading-tight">Maize Monitor</span><span className="mt-1 block text-xs text-ink-secondary">ADMIN CONSOLE</span></span>
          </Link>
          <div className="mx-4 mb-3 rounded-2xl bg-brand-tint p-4">
            <p className="m-0 text-[11px] font-bold uppercase tracking-[.16em] text-brand">Control room</p>
            <p className="mb-0 mt-1 text-sm leading-5 text-ink-secondary">Tools for keeping the field network healthy.</p>
          </div>
          <nav aria-label="Admin sections" className="flex flex-1 flex-col gap-1 overflow-y-auto px-4 py-3">
            {NAV_ITEMS.map(([section, label, icon]) => <NavItem key={section} section={section} label={label} icon={icon} activeSection={activeSection} onNavigate={() => { if (window.innerWidth < 1024) setSidebarVisible(false) }} />)}
          </nav>
          <div className="m-4 rounded-2xl border border-border bg-app-bg p-4">
            <div className="mb-3 flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-tint text-sm font-bold text-brand">{(name || 'A').slice(0, 1).toUpperCase()}</span>
              <div className="min-w-0"><p className="m-0 truncate text-sm font-bold">{name || 'Administrator'}</p>{phone && <p className="m-0 truncate text-xs text-ink-secondary">{phone}</p>}</div>
            </div>
            <button type="button" onClick={handleLogout} className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-left text-sm font-semibold hover:bg-neutral-bg">Log out</button>
          </div>
        </aside>}
        <div className="min-w-0 flex-1">
          <div className="sticky top-0 z-20 flex items-center justify-between border-b border-border/70 bg-surface/95 px-4 py-3 backdrop-blur sm:px-6">
            <div className="flex items-center gap-3">
              <button type="button" onClick={() => setSidebarVisible((visible) => !visible)} aria-label={sidebarVisible ? 'Hide sidebar' : 'Show sidebar'} aria-expanded={sidebarVisible} className="flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-surface text-lg text-ink hover:bg-neutral-bg">{sidebarVisible ? '‹' : '☰'}</button>
              <span className="text-sm font-semibold text-ink-secondary">Admin workspace <span className="mx-1 text-border">/</span> <span className="text-ink">{NAV_ITEMS.find(([key]) => key === activeSection)?.[1]}</span></span>
            </div>
            <button type="button" onClick={handleLogout} className="rounded-xl border border-border bg-surface px-3 py-2 text-sm font-semibold text-ink hover:bg-neutral-bg lg:hidden">Log out</button>
            <span className="hidden rounded-full bg-positive-bg px-3 py-1 text-xs font-bold text-positive-text sm:inline-flex">● System access active</span>
          </div>
          <main id="main-content" className="mx-auto w-full max-w-[1440px] p-4 sm:p-6 lg:p-8">{children}</main>
        </div>
      </div>
    </div>
  )
}
