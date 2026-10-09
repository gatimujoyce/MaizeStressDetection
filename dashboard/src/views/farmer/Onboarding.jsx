import { Navigate } from 'react-router-dom'
import { useFarm } from '../../farm/FarmContext'
import PlotWizard from './PlotWizard'

export default function Onboarding() {
  const { isLoading, hasFarms } = useFarm()

  if (isLoading) return <p>Checking your account...</p>
  if (hasFarms) return <Navigate to="/" replace />
  return <PlotWizard mode="onboarding" />
}
