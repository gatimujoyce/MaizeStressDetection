import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useFarm } from '../farm/FarmContext'
import Modal from './ui/Modal'
import { buttonClass, focusRing } from './ui/styles'

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

function formatAcres(acres) {
  if (acres === null || acres === undefined || acres === '') return ''
  return `${acres} ${Number(acres) === 1 ? 'acre' : 'acres'}`
}

// "My plots": choose which plot the screens show, or add another.
export default function PlotSwitcher() {
  const { farms, selectedFarmId, selectFarm } = useFarm()
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(true)}
        className={buttonClass({ variant: 'secondary' })}
      >
        My plots
        <ChevronDownIcon />
      </button>

      {isOpen && (
        <Modal title="Your plots" onClose={() => setIsOpen(false)}>
          <div className="flex flex-col gap-4">
            <ul className="m-0 list-none divide-y divide-border overflow-hidden rounded-card border border-border p-0">
              {farms.map((farm) => {
                const selected = farm.farm_id === selectedFarmId
                const details = [farm.county, formatAcres(farm.sizeAcres)].filter(Boolean).join(' · ')
                return (
                  <li key={farm.farm_id}>
                    <button
                      type="button"
                      aria-current={selected ? 'true' : undefined}
                      onClick={() => {
                        selectFarm(farm.farm_id)
                        setIsOpen(false)
                      }}
                      className={`flex min-h-14 w-full cursor-pointer items-center justify-between gap-3 rounded-none px-4 py-3 text-left ${focusRing} ${
                        selected ? 'bg-brand-tint' : 'bg-surface hover:bg-app-bg'
                      }`}
                    >
                      <span className="min-w-0">
                        <span className="block text-body font-bold text-ink">{farm.farm_name}</span>
                        {details && <span className="mt-1 block text-small font-normal text-ink-secondary">{details}</span>}
                      </span>
                      {selected && (
                        <span className="flex shrink-0 items-center gap-1 text-small font-bold text-brand">
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
                setIsOpen(false)
                navigate('/plots/new')
              }}
              className={buttonClass({ variant: 'secondary', block: true })}
            >
              Add another plot
            </button>
          </div>
        </Modal>
      )}
    </>
  )
}
