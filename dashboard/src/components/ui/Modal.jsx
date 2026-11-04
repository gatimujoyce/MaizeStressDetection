import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { focusRing } from './styles'

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

// A floating card over the page. Esc or a click outside closes it (unless dismissible is false); Tab stays inside it.
export default function Modal({ title, onClose, dismissible = true, wide = false, children }) {
  const panel = useRef(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    const opener = document.activeElement
    const scrollLock = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const first = panel.current?.querySelector('input, select, textarea') || panel.current
    first?.focus()

    function onKey(event) {
      if (event.key === 'Escape' && dismissible) {
        event.stopPropagation()
        onCloseRef.current?.()
        return
      }
      if (event.key !== 'Tab' || !panel.current) return
      const items = [...panel.current.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null)
      if (!items.length) { event.preventDefault(); return }
      const firstItem = items[0]
      const lastItem = items[items.length - 1]
      if (event.shiftKey && (document.activeElement === firstItem || document.activeElement === panel.current)) {
        event.preventDefault(); lastItem.focus()
      } else if (!event.shiftKey && document.activeElement === lastItem) {
        event.preventDefault(); firstItem.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = scrollLock
      if (opener && typeof opener.focus === 'function') opener.focus()
    }
  }, [dismissible])

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-ink/50 p-0 sm:items-center sm:p-4"
      onMouseDown={(event) => { if (dismissible && event.target === event.currentTarget) onClose?.() }}
    >
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className={`max-h-[92vh] w-full overflow-y-auto rounded-t-card bg-surface p-5 shadow-raised sm:rounded-card sm:p-6 ${wide ? 'sm:max-w-3xl' : 'sm:max-w-md'} ${focusRing}`}
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <h2 className="m-0 text-heading text-ink">{title}</h2>
          {dismissible && onClose && (
            <button type="button" onClick={onClose} aria-label="Close" className={`flex h-11 w-11 min-h-11 shrink-0 items-center justify-center rounded-control border-[1.5px] border-control bg-surface text-ink hover:bg-app-bg ${focusRing}`}>
              <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M6 6l12 12M18 6L6 18" /></svg>
            </button>
          )}
        </div>
        {children}
      </div>
    </div>,
    document.body,
  )
}
