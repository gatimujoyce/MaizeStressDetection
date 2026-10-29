import { useEffect, useState } from 'react'

// Current time that ticks every `intervalMs`, so "x min ago" and staleness stay
// correct while the page is open without calling Date.now() during render.
export default function useNow(intervalMs = 60000) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), intervalMs)
    return () => clearInterval(timer)
  }, [intervalMs])
  return now
}
