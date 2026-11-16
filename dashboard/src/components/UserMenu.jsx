import { useEffect, useId, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { focusRing } from './ui/styles'

function initialsOf(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '?'
  return ((parts[0][0] || '') + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase()
}

const itemClass = `flex min-h-12 w-full cursor-pointer items-center rounded-control bg-transparent px-3 text-left text-body font-bold text-ink no-underline hover:bg-app-bg ${focusRing}`

// The signed-in person's menu in the top bar: their initials open Profile and Sign out.
// Esc or a click outside closes it and puts focus back on the button; the arrow keys move between items.
export default function UserMenu({ profilePath }) {
  const { name, phone, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const button = useRef(null)
  const menu = useRef(null)
  const menuId = useId()

  const close = (returnFocus = true) => {
    setOpen(false)
    if (returnFocus) button.current?.focus()
  }

  useEffect(() => {
    if (!open) return undefined
    menu.current?.querySelector('[role="menuitem"]')?.focus()
    const onPointer = (event) => {
      if (!menu.current?.contains(event.target) && !button.current?.contains(event.target)) setOpen(false)
    }
    document.addEventListener('pointerdown', onPointer)
    return () => document.removeEventListener('pointerdown', onPointer)
  }, [open])

  const onMenuKeyDown = (event) => {
    const items = [...(menu.current?.querySelectorAll('[role="menuitem"]') ?? [])]
    const at = items.indexOf(document.activeElement)
    if (event.key === 'Escape') {
      event.preventDefault()
      close()
    } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      const step = event.key === 'ArrowDown' ? 1 : -1
      items[(at + step + items.length) % items.length]?.focus()
    } else if (event.key === 'Tab') {
      close(false)
    }
  }

  const signOut = () => {
    setOpen(false)
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="relative">
      <button
        ref={button}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        aria-label={`Account menu for ${name || 'you'}`}
        onClick={() => setOpen((value) => !value)}
        className={`flex h-11 w-11 cursor-pointer items-center justify-center rounded-full border-[1.5px] border-control bg-surface text-small font-bold text-ink hover:bg-app-bg ${focusRing}`}
      >
        <span aria-hidden="true">{initialsOf(name)}</span>
      </button>
      {open && (
        <div
          ref={menu}
          id={menuId}
          role="menu"
          aria-label="Account"
          onKeyDown={onMenuKeyDown}
          className="absolute right-0 top-full z-50 mt-2 w-64 max-w-[calc(100vw-2rem)] rounded-card border border-border bg-surface p-2 shadow-raised"
        >
          <div className="border-b border-border px-3 pb-3 pt-2">
            <p className="m-0 truncate text-body font-bold text-ink">{name || 'Your account'}</p>
            {phone && <p className="m-0 truncate text-small tabular-nums text-ink-secondary">{phone}</p>}
          </div>
          <div className="flex flex-col gap-1 pt-2">
            <Link role="menuitem" to={profilePath} onClick={() => setOpen(false)} className={itemClass}>
              Profile
            </Link>
            <button role="menuitem" type="button" onClick={signOut} className={itemClass}>
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
