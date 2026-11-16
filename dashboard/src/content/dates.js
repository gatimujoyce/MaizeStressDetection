// Date wording for the farmer screens, in one place so every screen says it the same way.

const timeOf = (value) => {
  const t = Date.parse(value)
  return Number.isNaN(t) ? null : t
}

// "12 Nov 2026"
export function formatDay(value) {
  const t = timeOf(value)
  return t === null ? '' : new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }).format(t)
}

// "just now", "5 min ago", "3 hours ago", "2 days ago". Pass `now` from useNow() so it stays current.
export function timeAgo(value, now = Date.now()) {
  const t = timeOf(value)
  if (t === null) return ''
  const minutes = Math.max(0, Math.round((now - t) / 60000))
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`
  const days = Math.floor(hours / 24)
  return `${days} ${days === 1 ? 'day' : 'days'} ago`
}

// "2 hours ago" for the last few hours, "Today 5:07 pm", "Yesterday 5:07 pm", then "12 Oct 5:07 pm".
export function formatWhen(value, now = Date.now()) {
  const t = timeOf(value)
  if (t === null) return ''
  const date = new Date(t)
  const today = new Date(now)
  const minutes = Math.round((now - t) / 60000)
  const clock = date.toLocaleTimeString('en-KE', { hour: 'numeric', minute: '2-digit' })
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes} min ago`
  if (minutes < 360) return `${Math.floor(minutes / 60)} hours ago`
  const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  if (date >= startOfToday) return `Today ${clock}`
  const startOfYesterday = new Date(startOfToday - 86400000)
  if (date >= startOfYesterday) return `Yesterday ${clock}`
  return `${date.toLocaleDateString('en-KE', { day: 'numeric', month: 'short' })} ${clock}`
}
