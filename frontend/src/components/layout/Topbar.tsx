export function Topbar({
  title,
  subtitle,
  onMenuClick,
}: {
  title: string
  subtitle: string
  onMenuClick: () => void
}) {
  return (
    <header className="h-16 bg-card border-b border-card-border flex items-center justify-between px-4 md:px-6 sticky top-0 z-10">
      <div className="flex items-center gap-3">
        <button onClick={onMenuClick} className="md:hidden text-ink" aria-label="打开菜单">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </button>
        <div>
          <h1 className="text-base md:text-lg font-semibold text-ink leading-tight">{title}</h1>
          <p className="text-xs text-sub">{subtitle}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <input
          className="hidden md:block w-56 px-3 py-1.5 text-sm rounded-lg bg-bg border border-card-border focus:outline-none focus:ring-2 focus:ring-primary/40"
          placeholder="搜索..."
        />
        <button className="relative text-sub hover:text-ink transition-colors" aria-label="通知">
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-danger" />
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.7 21a2 2 0 0 1-3.4 0" />
          </svg>
        </button>
        <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-sm font-medium">
          管
        </div>
      </div>
    </header>
  )
}
