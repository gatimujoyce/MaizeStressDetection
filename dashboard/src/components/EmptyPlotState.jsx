import { Link } from 'react-router-dom'
import MaizePlant from './illustrations/MaizePlant'
import { buttonClass } from './ui/styles'

export default function EmptyPlotState({ plotName }) {
  return (
    <section className="flex flex-col items-center rounded-card bg-brand-tint p-6 text-center text-ink">
      <MaizePlant variant="seedling" className="mb-4 w-36 mx-auto" />
      <h2 className="mb-2 text-title">No checks yet for {plotName}</h2>
      <p className="mb-5 mt-0 text-body">
        Take a photo of a maize leaf and we will tell you how your plant is doing.
      </p>
      <Link
        to="/check-in"
        className={`${buttonClass({ block: true })} sm:w-auto`}
      >
        Take your first photo
      </Link>
    </section>
  )
}
