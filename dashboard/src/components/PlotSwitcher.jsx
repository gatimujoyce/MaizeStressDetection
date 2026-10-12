import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useFarm } from '../farm/FarmContext'

function ChevronDownIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
      <path d="m6 9 6 6 6-6" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="h-5 w-5">
      <path d="m5 12 4 4L19 6" />
    </svg>
  )
}

function PlusIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-5 w-5">
      <path d="M12 5v14M5 12h14" />
    </svg>
  )
}

function formatAcres(acres) {
  if (acres === null || acres === undefined || acres === '') return ''
  return `${acres} ${Number(acres) === 1 ? 'acre' : 'acres'}`
}

export default function PlotSwitcher() {
  const { farms, selectedFarmId, selectFarm } = useFarm()
  const navigate = useNavigate()
  const triggerRef = useRef(null)
  const dialogRef = useRef(null)
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (isOpen && !dialog.open) dialog.showModal()
    if (!isOpen && dialog.open) dialog.close()
  }, [isOpen])

  const closeDialog = () => {
    setIsOpen(false)
    requestAnimationFrame(() => triggerRef.current?.focus())
  }

  const handleDialogClick = (event) => {
    if (event.target === dialogRef.current) closeDialog()
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(true)}
        className="flex min-h-12 items-center justify-center gap-2 rounded-xl border-2 border-brand bg-surface px-4 text-base font-semibold text-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
      >
        My plots
        <ChevronDownIcon />
      </button>

      <dialog
        ref={dialogRef}
        aria-labelledby="your-plots-title"
        onCancel={() => setIsOpen(false)}
        onKeyDown={(event) => {
          if (event.key === 'Escape') closeDialog()
        }}
        onClick={handleDialogClick}
        onClose={() => {
          setIsOpen(false)
          requestAnimationFrame(() => triggerRef.current?.focus())
        }}
        className="fixed inset-x-0 bottom-0 top-auto m-0 max-h-[80vh] w-full max-w-none overflow-y-auto rounded-t-3xl border-0 bg-surface p-5 text-ink backdrop:bg-black/40 sm:inset-0 sm:m-auto sm:max-w-md sm:rounded-3xl"
      >
        <div className="flex flex-col gap-5">
          <header className="flex items-center justify-between gap-3">
            <h2 id="your-plots-title" className="m-0 text-2xl font-bold">Your plots</h2>
            <button
              type="button"
              onClick={closeDialog}
              className="min-h-12 rounded-xl px-4 text-base font-semibold text-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
            >
              Close
            </button>
          </header>

          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {farms.map((farm) => {
              const selected = farm.farm_id === selectedFarmId
              const details = [farm.county, formatAcres(farm.sizeAcres)].filter(Boolean).join(' - ')
              return (
                <li key={farm.farm_id}>
                  <button
                    type="button"
                    aria-current={selected ? 'true' : undefined}
                    onClick={() => {
                      selectFarm(farm.farm_id)
                      closeDialog()
                    }}
                    className={`flex min-h-14 w-full items-center justify-between gap-3 rounded-xl border px-4 py-3 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand ${
                      selected ? 'border-2 border-brand bg-brand-tint' : 'border-border bg-surface'
                    }`}
                  >
                    <span className="min-w-0">
                      <span className="block text-base font-bold">{farm.farm_name}</span>
                      {details && <span className="mt-1 block text-base text-ink-secondary">{details}</span>}
                    </span>
                    {selected && (
                      <span className="flex shrink-0 items-center gap-1 text-base font-semibold text-brand">
                        <CheckIcon />
                        Selected
                      </span>
                    )}
                  </button>
                </li>
              )
            })}
          </ul>

          <button
            type="button"
            onClick={() => {
              closeDialog()
              navigate('/plots/new')
            }}
            className="flex min-h-12 items-center justify-center gap-2 rounded-xl border-2 border-brand bg-surface px-4 text-base font-semibold text-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
          >
            <PlusIcon />
            Add another plot
          </button>
        </div>
      </dialog>
    </>
  )
}
