import { Link } from 'react-router-dom'
import MaizePlant from './illustrations/MaizePlant'

export default function EmptyPlotState({ plotName }) {
  return (
    <section className="flex flex-col items-center rounded-[24px] bg-brand-tint p-6 text-center text-ink">
      <MaizePlant variant="seedling" className="mb-4 w-36 mx-auto" />
      <h2 className="mb-2 text-2xl font-bold">No checks yet for {plotName}</h2>
      <p className="mb-5 text-[17px]">
        Take a photo of a maize leaf and we will tell you how your plant is doing.
      </p>
      <Link
        to="/check-in"
        className="flex min-h-[52px] w-full items-center justify-center rounded-xl bg-brand px-5 py-3 text-center text-[17px] font-bold text-white hover:bg-brand-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand sm:w-auto"
      >
        Take your first photo
      </Link>
    </section>
  )
}
