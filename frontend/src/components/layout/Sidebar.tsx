import { NavLink } from 'react-router-dom'
import { menuItems } from '../../theme'

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-sidebar text-white flex flex-col">
      <div className="h-16 flex items-center px-5 text-lg font-semibold border-b border-white/10 shrink-0">
        智备货 StockWise
      </div>
      <nav className="flex-1 py-3 overflow-y-auto">
        {menuItems.map((item) => (
          <NavLink
            key={item.key}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `block px-5 py-3 text-sm transition-colors border-l-4 ${
                isActive
                  ? 'bg-sidebar-active border-primary text-white'
                  : 'border-transparent text-white/70 hover:bg-white/5 hover:text-white'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
