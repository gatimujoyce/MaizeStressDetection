import { Navigate } from 'react-router-dom'
import { useFarm } from '../../farm/FarmContext'
import Page from '../../components/ui/Page'
import Skeleton from '../../components/ui/Skeleton'
import PlotWizard from './PlotWizard'

// First sign-in with no plot yet: set one up.
export default function Onboarding() {
  const { isLoading, hasFarms } = useFarm()
  if (isLoading) {
    return (
      <Page>
        <Skeleton label="Checking your account" className="h-96" />
      </Page>
    )
  }
  if (hasFarms) return <Navigate to="/" replace />
  return <PlotWizard mode="onboarding" />
}
