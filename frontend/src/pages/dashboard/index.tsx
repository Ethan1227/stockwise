import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getSummary } from '../../api/dashboard'

const KPI_CARDS = [
  { key: 'sku_count', label: '在售 SKU', color: '#6366F1', icon: '📦' },
  { key: 'suggest_count', label: '建议备货 SKU', color: '#10B981', icon: '🛒' },
  { key: 'stockout', label: '缺货预警', color: '#EF4444', icon: '🚨' },
  { key: 'slow', label: '滞销预警', color: '#F59E0B', icon: '🐌' },
] as const

const TODO_STYLE: Record<string, string> = {
  紧急缺货: 'bg-danger',
  数据未更新: 'bg-warning',
  待确认采购单: 'bg-info',
  大促: 'bg-primary',
}

export function Dashboard() {
  const navigate = useNavigate()
  const { data } = useQuery({ queryKey: ['dashboard-summary'], queryFn: getSummary })

  if (!data) return <div className="text-sub">加载中…</div>

  return (
    <div className="space-y-6">
      {/* KPI 卡 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {KPI_CARDS.map((c) => (
          <div key={c.key} className="bg-card border border-card-border rounded-xl p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="w-10 h-10 rounded-lg flex items-center justify-center text-lg" style={{ backgroundColor: `${c.color}15` }}>
                {c.icon}
              </span>
            </div>
            <div className="text-2xl font-semibold text-ink">{data.kpi[c.key]}</div>
            <div className="text-sm text-sub">{c.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* 销量趋势 */}
        <div className="lg:col-span-2 bg-card border border-card-border rounded-xl p-5">
          <h3 className="font-semibold text-ink mb-4">全店销量趋势（近 30 天）</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.sales_series}>
                <defs>
                  <linearGradient id="amazon" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="walmart" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E6E9F2" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#8A90A6' }} tickFormatter={(v: string) => v.slice(5)} />
                <YAxis tick={{ fontSize: 11, fill: '#8A90A6' }} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="amazon" name="亚马逊" stroke="#6366F1" fill="url(#amazon)" />
                <Area type="monotone" dataKey="walmart" name="沃尔玛" stroke="#10B981" fill="url(#walmart)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 数据接入状态 */}
        <div className="bg-card border border-card-border rounded-xl p-5">
          <h3 className="font-semibold text-ink mb-4">数据接入状态</h3>
          <div className="space-y-3">
            {data.datasources.map((d) => (
              <div key={d.source_code} className="flex items-center justify-between">
                <span className="text-sm text-ink">{d.name}</span>
                <span className={`inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full ${d.status === '已连接' ? 'bg-success/10 text-success' : 'bg-sub/10 text-sub'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${d.status === '已连接' ? 'bg-success' : 'bg-sub'}`} />
                  {d.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 今日待办 */}
      <div className="bg-card border border-card-border rounded-xl p-5">
        <h3 className="font-semibold text-ink mb-4">今日待办</h3>
        <div className="space-y-2">
          {data.todos.map((t, i) => (
            <button
              key={i}
              onClick={() => navigate(t.route)}
              className="w-full flex items-center gap-3 rounded-lg bg-bg/50 px-4 py-3 text-left hover:bg-bg"
            >
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: TODO_STYLE[t.type] ?? '#3B82F6' }} />
              <span className="text-xs text-sub w-20 shrink-0">{t.type}</span>
              <span className="text-sm text-ink flex-1">{t.text}</span>
              <span className="text-xs text-primary">去处理 →</span>
            </button>
          ))}
          {data.todos.length === 0 && <div className="text-sub text-sm">暂无待办</div>}
        </div>
      </div>
    </div>
  )
}
