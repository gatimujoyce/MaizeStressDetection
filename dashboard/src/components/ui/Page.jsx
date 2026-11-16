// The farmer page frame: the same width and vertical rhythm on every screen. The side gutters come from Layout.
export default function Page({ children, className = '' }) {
  return <div className={`mx-auto flex w-full max-w-farmer flex-col gap-stack ${className}`}>{children}</div>
}
