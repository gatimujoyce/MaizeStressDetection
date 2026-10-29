import { useEffect, useState } from 'react'
import Notice from './ui/Notice'

// Shown on every farmer screen while the phone has no connection.
export default function OfflineNotice() {
  const [isOffline, setIsOffline] = useState(!navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOffline(false)
    const handleOffline = () => setIsOffline(true)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  if (!isOffline) return null
  return (
    <Notice tone="neutral" className="mb-6">
      <p>You are offline. Showing the last data saved on your phone.</p>
    </Notice>
  )
}
