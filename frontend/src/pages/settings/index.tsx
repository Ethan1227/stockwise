import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { getSettings, updateSettings } from '../../api/settings'
import type { PromotionEvent } from '../../api/settings'
import { createSku, deleteSku, listSkus, updateSku } from '../../api/skus'
import type { Sku } from '../../api/skus'

const PLATFORMS = ['亚马逊', '沃尔玛', '双平台']

const SKU_FIELDS: { key: keyof Sku; label: string; type?: string }[] = [
  { key: 'name', label: '品名' },
  { key: 'category', label: '类目' },
  { key: 'supplier', label: '供应商' },
  { key: 'unit_cost', label: '成本', type: 'number' },
  { key: 'price', label: '售价', type: 'number' },
  { key: 'moq', label: 'MOQ', type: 'number' },
  { key: 'lead_prod_days', label: '生产天数', type: 'number' },
  { key: 'lead_ship_days', label: '头程天数', type: 'number' },
  { key: 'safety_days', label: '安全天数', type: 'number' },
]

export function Settings() {
  const [tab, setTab] = useState<'skus' | 'params'>('skus')
  return (
    <div>
      <div className="flex gap-2 mb-5">
        {[
          { key: 'skus', label: '商品档案' },
          { key: 'params', label: '业务参数' },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key as 'skus' | 'params')}
            className={`rounded-full px-4 py-1.5 text-sm font-medium ${
              tab === t.key ? 'bg-primary text-white' : 'bg-card border border-card-border text-ink'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === 'skus' ? <SkuManager /> : <ParamEditor />}
    </div>
  )
}

// ---- 商品档案（SKU 管理）----
function SkuManager() {
  const queryClient = useQueryClient()
  const { data: skus, isLoading } = useQuery({ queryKey: ['skus'], queryFn: listSkus })
  const [editing, setEditing] = useState<Sku | null>(null)
  const [creating, setCreating] = useState(false)
  const [toast, setToast] = useState('')

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['skus'] })

  const createMutation = useMutation({ mutationFn: createSku, onSuccess: () => { setCreating(false); setToast('已新增'); invalidate() } })
  const updateMutation = useMutation({ mutationFn: ({ sku, body }: { sku: string; body: Partial<Sku> }) => updateSku(sku, body), onSuccess: () => { setEditing(null); setToast('已保存'); invalidate() } })
  const deleteMutation = useMutation({ mutationFn: deleteSku, onSuccess: () => { setToast('已删除'); invalidate() } })

  if (isLoading) return <div className="text-sub">加载中…</div>

  return (
    <div>
      {toast && <div className="mb-4 rounded-lg px-4 py-2.5 text-sm bg-success/10 text-success">{toast}</div>}
      <div className="flex justify-end mb-3">
        <button onClick={() => setCreating(true)} className="rounded-lg bg-primary text-white px-4 py-2 text-sm hover:opacity-90">新增 SKU</button>
      </div>
      <div className="bg-card border border-card-border rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-bg/60 text-sub text-left">
            <tr>
              <th className="px-4 py-3 font-medium">SKU</th>
              <th className="px-4 py-3 font-medium">品名</th>
              <th className="px-4 py-3 font-medium">平台</th>
              <th className="px-4 py-3 font-medium">类目</th>
              <th className="px-4 py-3 font-medium">供应商</th>
              <th className="px-4 py-3 font-medium">成本/售价</th>
              <th className="px-4 py-3 font-medium">MOQ</th>
              <th className="px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-card-border">
            {skus?.map((s) => (
              <tr key={s.sku} className="hover:bg-bg/40">
                <td className="px-4 py-3 font-medium text-ink">{s.sku}</td>
                <td className="px-4 py-3 text-ink">{s.name}</td>
                <td className="px-4 py-3 text-sub">{s.platform}</td>
                <td className="px-4 py-3 text-sub">{s.category}</td>
                <td className="px-4 py-3 text-sub">{s.supplier}</td>
                <td className="px-4 py-3 text-ink">¥{s.unit_cost} / ¥{s.price}</td>
                <td className="px-4 py-3 text-ink">{s.moq}</td>
                <td className="px-4 py-3 flex gap-2">
                  <button onClick={() => setEditing(s)} className="text-xs rounded-lg bg-primary/10 text-primary px-3 py-1.5">编辑</button>
                  <button onClick={() => deleteMutation.mutate(s.sku)} className="text-xs rounded-lg bg-danger/10 text-danger px-3 py-1.5">删除</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(creating || editing) && (
        <SkuForm
          initial={editing ?? undefined}
          onClose={() => { setCreating(false); setEditing(null) }}
          onSubmit={(body) => {
            if (editing) updateMutation.mutate({ sku: editing.sku, body })
            else createMutation.mutate(body)
          }}
        />
      )}
    </div>
  )
}

function SkuForm({ initial, onClose, onSubmit }: { initial?: Sku; onClose: () => void; onSubmit: (body: Partial<Sku>) => void }) {
  const [form, setForm] = useState<Partial<Sku>>(initial ?? { sku: '', name: '', platform: '亚马逊', moq: 1, lead_ship_days: 35, safety_days: 10 })

  function set(key: keyof Sku, value: string | number) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <div className="absolute inset-0 bg-black/30" />
      <div className="absolute right-0 top-0 h-full w-96 bg-card shadow-xl p-6 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-ink">{initial ? `编辑 ${initial.sku}` : '新增 SKU'}</h3>
          <button onClick={onClose} className="text-sub hover:text-ink">✕</button>
        </div>
        <div className="space-y-3">
          <label className="block text-sm">
            <span className="text-sub">SKU 编码</span>
            <input value={form.sku} disabled={!!initial} onChange={(e) => set('sku', e.target.value)} className="mt-1 w-full rounded-lg border border-card-border px-3 py-2 text-sm disabled:bg-bg" />
          </label>
          <label className="block text-sm">
            <span className="text-sub">平台</span>
            <select value={form.platform} onChange={(e) => set('platform', e.target.value)} className="mt-1 w-full rounded-lg border border-card-border px-3 py-2 text-sm">
              {PLATFORMS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </label>
          {SKU_FIELDS.map((f) => (
            <label key={f.key} className="block text-sm">
              <span className="text-sub">{f.label}</span>
              <input
                type={f.type ?? 'text'}
                value={form[f.key] ?? ''}
                onChange={(e) => set(f.key, f.type === 'number' ? Number(e.target.value) : e.target.value)}
                className="mt-1 w-full rounded-lg border border-card-border px-3 py-2 text-sm"
              />
            </label>
          ))}
          <button onClick={() => onSubmit(form)} className="w-full rounded-lg bg-primary text-white px-4 py-2 text-sm hover:opacity-90">保存</button>
        </div>
      </div>
    </div>
  )
}

// ---- 业务参数 ----
function ParamEditor() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['settings'], queryFn: getSettings })
  const [form, setForm] = useState<Record<string, unknown> | null>(null)
  const [calendar, setCalendar] = useState<PromotionEvent[]>([])
  const [toast, setToast] = useState('')

  useEffect(() => {
    if (data) {
      setForm(data as unknown as Record<string, unknown>)
      setCalendar(data.promotion_calendar ?? [])
    }
  }, [data])

  const mutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => { setToast('已保存'); queryClient.invalidateQueries({ queryKey: ['settings'] }) },
  })

  if (isLoading || !form) return <div className="text-sub">加载中…</div>

  const w = (form.base_weights as { '30d': number; '90d': number; yoy: number }) ?? { '30d': 0.5, '90d': 0.3, yoy: 0.2 }
  const tiers = (form.modifier_tiers as Record<string, Record<string, number>>) ?? {}

  function setNum(key: string, value: number) {
    setForm((f) => ({ ...f, [key]: value }))
  }
  function setWeight(key: '30d' | '90d' | 'yoy', value: number) {
    setForm((f) => ({ ...f, base_weights: { ...(f!.base_weights as object), [key]: value } }))
  }
  function setTier(group: string, key: string, value: number) {
    setForm((f) => ({ ...f, modifier_tiers: { ...(f!.modifier_tiers as object), [group]: { ...(tiers[group] ?? {}), [key]: value } } }))
  }

  function save() {
    const body = { ...form, promotion_calendar: calendar }
    mutation.mutate(body)
  }

  return (
    <div className="space-y-5 max-w-3xl">
      {toast && <div className="rounded-lg px-4 py-2.5 text-sm bg-success/10 text-success">{toast}</div>}

      <div className="bg-card border border-card-border rounded-xl p-5">
        <h3 className="font-semibold text-ink mb-4">基线权重</h3>
        <div className="grid grid-cols-3 gap-3">
          <NumField label="近 30 天" value={w['30d']} onChange={(v) => setWeight('30d', v)} />
          <NumField label="近 90 天" value={w['90d']} onChange={(v) => setWeight('90d', v)} />
          <NumField label="去年同期" value={w.yoy} onChange={(v) => setWeight('yoy', v)} />
        </div>
      </div>

      <div className="bg-card border border-card-border rounded-xl p-5">
        <h3 className="font-semibold text-ink mb-4">备货周期与预算</h3>
        <div className="grid grid-cols-3 gap-3">
          <NumField label="安全天数" value={form.safety_days as number} onChange={(v) => setNum('safety_days', v)} />
          <NumField label="海运头程(天)" value={form.lead_transit_sea as number} onChange={(v) => setNum('lead_transit_sea', v)} />
          <NumField label="空运头程(天)" value={form.lead_transit_air as number} onChange={(v) => setNum('lead_transit_air', v)} />
          <NumField label="上架天数" value={form.lead_shelf_days as number} onChange={(v) => setNum('lead_shelf_days', v)} />
          <NumField label="月采购预算(元)" value={form.monthly_budget as number} onChange={(v) => setNum('monthly_budget', v)} />
        </div>
      </div>

      <div className="bg-card border border-card-border rounded-xl p-5">
        <h3 className="font-semibold text-ink mb-4">修正器档位</h3>
        <div className="grid grid-cols-4 gap-3">
          {tiers.trend && (['strong_up', 'up', 'flat', 'down'] as const).map((k) => (
            <NumField key={k} label={`趋势·${k}`} value={tiers.trend[k]} onChange={(v) => setTier('trend', k, v)} />
          ))}
          {tiers.competitor && (['stockout', 'price_cut'] as const).map((k) => (
            <NumField key={k} label={`竞争·${k}`} value={tiers.competitor[k]} onChange={(v) => setTier('competitor', k, v)} />
          ))}
          {tiers.event && (['hot', 'near'] as const).map((k) => (
            <NumField key={k} label={`大促·${k}`} value={tiers.event[k]} onChange={(v) => setTier('event', k, v)} />
          ))}
          {tiers.env && (['min', 'max'] as const).map((k) => (
            <NumField key={k} label={`环境·${k}`} value={tiers.env[k]} onChange={(v) => setTier('env', k, v)} />
          ))}
        </div>
      </div>

      <div className="bg-card border border-card-border rounded-xl p-5">
        <h3 className="font-semibold text-ink mb-4">大促日历</h3>
        <div className="space-y-2">
          {calendar.map((ev, i) => (
            <div key={i} className="flex gap-2 items-center">
              <input value={ev.event} onChange={(e) => setCalendar((c) => c.map((x, j) => j === i ? { ...x, event: e.target.value } : x))} className="flex-1 rounded-lg border border-card-border px-3 py-1.5 text-sm" placeholder="大促名" />
              <input type="date" value={ev.event_date} onChange={(e) => setCalendar((c) => c.map((x, j) => j === i ? { ...x, event_date: e.target.value } : x))} className="rounded-lg border border-card-border px-3 py-1.5 text-sm" />
              <input type="date" value={ev.warehouse_deadline} onChange={(e) => setCalendar((c) => c.map((x, j) => j === i ? { ...x, warehouse_deadline: e.target.value } : x))} className="rounded-lg border border-card-border px-3 py-1.5 text-sm" />
              <button onClick={() => setCalendar((c) => c.filter((_, j) => j !== i))} className="text-xs text-danger">删除</button>
            </div>
          ))}
          <button onClick={() => setCalendar((c) => [...c, { event: '', event_date: '', warehouse_deadline: '' }])} className="text-sm text-primary">+ 新增大促</button>
        </div>
      </div>

      <button onClick={save} disabled={mutation.isPending} className="rounded-lg bg-primary text-white px-5 py-2 text-sm hover:opacity-90 disabled:opacity-60">
        {mutation.isPending ? '保存中…' : '保存参数'}
      </button>
    </div>
  )
}

function NumField({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <label className="block text-sm">
      <span className="text-sub">{label}</span>
      <input type="number" value={value} onChange={(e) => onChange(Number(e.target.value))} className="mt-1 w-full rounded-lg border border-card-border px-3 py-2 text-sm" />
    </label>
  )
}
