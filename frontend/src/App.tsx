import { Route, Routes, useLocation } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { Topbar } from './components/layout/Topbar'
import { menuItems } from './theme'
import { Dashboard } from './pages/dashboard'
import { DataCenter } from './pages/datacenter'
import { Suggestions } from './pages/suggestions'
import { Alerts } from './pages/alerts'
import { Purchase } from './pages/purchase'
import { Chat } from './pages/chat'
import { Settings } from './pages/settings'

export default function App() {
  const { pathname } = useLocation()
  const current = menuItems.find((m) =>
    m.path === '/' ? pathname === '/' : pathname.startsWith(m.path),
  )

  return (
    <div className="min-h-screen bg-bg">
      <Sidebar />
      <div className="ml-60">
        <Topbar title={current?.label ?? ''} subtitle="智备货 StockWise" />
        <main className="p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/datacenter" element={<DataCenter />} />
            <Route path="/suggestions" element={<Suggestions />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/purchase" element={<Purchase />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
