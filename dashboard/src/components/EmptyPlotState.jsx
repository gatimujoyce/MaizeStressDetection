import { Link } from 'react-router-dom'
import MaizePlant from './illustrations/MaizePlant'
import Card from './ui/Card'
import { buttonClass } from './ui/styles'

// A plot with no photo checks yet. The one place on Home that keeps the illustration.
export default function EmptyPlotState({ plotName }) {
  return (
    <Card className="flex flex-col items-center text-center">
      <MaizePlant variant="seedling" className="mx-auto mb-4 w-32" />
      <h2 className="m-0 mb-2 text-section text-ink">No checks yet for {plotName}</h2>
      <p className="m-0 mb-6 max-w-prose text-body text-ink-secondary">
        Take a photo of a maize leaf and we will tell you how your plant is doing.
      </p>
      <Link to="/check-in" className={`${buttonClass({ block: true })} sm:w-auto`}>
        Take your first photo
      </Link>
    </Card>
  )
}
