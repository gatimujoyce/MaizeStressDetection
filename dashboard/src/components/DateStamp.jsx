export default function DateStamp({ date }) {
  if (!date) return null

  const parsed = new Date(date)
  if (Number.isNaN(parsed.getTime())) return null

  const shortFormatter = new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
  })
  const longFormatter = new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'long',
  })

  return (
    <div
      role="img"
      aria-label={`Last checked ${longFormatter.format(parsed)}`}
      className="relative inline-block -rotate-[3deg] rounded-md border-2 border-brand px-3 py-[6px] text-brand"
    >
      <div aria-hidden="true" className="pointer-events-none absolute inset-[3px] rounded-[4px] border border-brand" />
      <div className="text-center">
        <div className="text-[15px] font-bold uppercase leading-none tracking-[0.06em]">Checked</div>
        <div className="mt-1 text-[20px] font-bold leading-none">{shortFormatter.format(parsed)}</div>
      </div>
    </div>
  )
}
