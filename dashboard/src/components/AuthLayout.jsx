import MaizePlant from './illustrations/MaizePlant'

export default function AuthLayout({ children, subtitle }) {
  return (
    <div className="relative min-h-screen bg-app-bg md:grid md:grid-cols-[45%_55%]">
      <picture className="relative block h-44 w-full md:absolute md:inset-y-0 md:left-0 md:h-full md:w-[45%]">
        <source media="(min-width: 768px)" srcSet="/images/hero-field-portrait.webp" />
        <img
          src="/images/hero-field-landscape.webp"
          alt=""
          width="1440"
          height="640"
          loading="eager"
          fetchPriority="high"
          className="h-full w-full object-cover"
        />
        <div className="absolute inset-0 hidden bg-gradient-to-t from-black/70 to-transparent md:block" />
        <div className="absolute bottom-0 left-0 hidden p-8 text-white md:block lg:p-10">
          <p className="mb-2 text-[28px] font-bold">Know how your maize is doing.</p>
          <p className="text-[17px]">Take a photo of a maize leaf and get clear advice for your field.</p>
        </div>
      </picture>
      <div className="relative z-10 -mt-8 bg-app-bg px-4 pb-8 md:col-start-2 md:row-start-1 md:mt-0 md:flex md:min-h-screen md:items-center md:justify-center md:px-8 md:py-8">
        <section className="mx-auto w-full max-w-sm rounded-t-3xl border border-border bg-surface p-6 sm:p-8 md:rounded-2xl">
          <header className="mb-6 text-center">
            <MaizePlant variant="seedling" className="mx-auto mb-2 h-10 w-10" />
            <p className="m-0 text-2xl font-bold text-brand">MaizeStressMonitor</p>
            <p className="mt-1 text-[15px] text-ink-secondary">{subtitle}</p>
          </header>
          {children}
        </section>
      </div>
    </div>
  )
}
