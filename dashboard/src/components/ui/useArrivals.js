import { useState } from 'react'

// Remembers which keys were on screen when the data first loaded (pass the query's isSuccess,
// not !isLoading: a disabled query is "not loading" with an empty list). Anything that shows up
// after that (e.g. an alert arriving on the 15s poll) counts as an arrival and can animate in.
export default function useArrivals(keys, ready) {
  const [initial, setInitial] = useState(null)
  if (ready && initial === null) setInitial(new Set(keys))
  return (key) => initial !== null && !initial.has(key)
}
