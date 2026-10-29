import { Navigate } from 'react-router-dom'
import { useFarm } from '../../farm/FarmContext'
import Skeleton from '../../components/ui/Skeleton'
import PlotWizard from './PlotWizard'

export default function Onboarding() {
  const { isLoading, hasFarms } = useFarm()

  if (isLoading) return <Skeleton label="Checking your account..." className="mx-auto h-96 max-w-2xl" />
  if (hasFarms) return <Navigate to="/" replace />
  return <PlotWizard mode="onboarding" />
}
