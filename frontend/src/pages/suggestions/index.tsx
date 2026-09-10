import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { Suggestion } from '../../api/suggestions'
import { listSuggestions, triggerCalc, updateSuggestion } from '../../api/suggestions'
import { ScoreBadge } from '../../components/ui/Badge'

const BANDS = ['立即补货', '常规', '观望', '停止补货']
const PLATFORMS = ['亚马逊', '沃尔玛', '双平台']

export function Suggestions() {
  const queryClient = useQueryClient()
  const [platform, setPlatform] = useState('')
  const [scoreBand, setScoreBand] = useState('')
  const [selected, setSelected] = useState<Suggestion | null>(null)
  const [adjustQty, setAdjustQty] = useState('')
  const [toast, setToast] = useState('')

  const { data: rows, isLoading } = useQuery({
    queryKey: ['suggestions', platform, scoreBand],
    queryFn: () => listSuggestions({ platform: platform || undefined, score_band: scoreBand || undefined }),
  })

  const calcMutation = useMutation({
    mutationFn: triggerCalc,
    onSuccess: (data) => {
      setToast(`重新测算完成（${data.count} 个 SKU）`)
      queryClient.invalidateQueries({ queryKey: ['suggestions'] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ sku, qty }: { sku: string; qty: number | null }) => updateSuggestion(sku, { adjusted_qty: qty }),
    onSuccess: () => {
      setToast('已保存调整')
      setSelected(null)
      setAdjustQty('')
      queryClient.invalidateQueries({ queryKey: ['suggestions'] })
    },
  })

  function ignore(sku: string) {
    updateMutation.mutate({ sku, qty: null })
  }

  function exportExcel() {
    window.location.href = '/api/suggestions/export'
  }

  return (
    <div>
      {toast && (
        <div className="mb-4 rounded-lg px-4 py-2.5 text-sm bg-primary/10 text-primary border border-primary/20">{toast}</div>
      )}

      {/* 筛选条 */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <select value={platform} onChange={(e) => setPlatform(e.target.value)} className="rounded-lg border border-card-border bg-card px-3 py-2 text-sm text-ink">
          <option value="">全部平台</option>
          {PLATFORMS.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <select value={scoreBand} onChange={(e) => setScoreBand(e.target.value)} className="rounded-lg border border-card-border bg-card px-3 py-2 text-sm text-ink">
          <option value="">全部评分档</option>
          {BANDS.map((b) => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
        <div className="flex-1" />
        <button onClick={() => calcMutation.mutate()} disabled={calcMutation.isPending} className="rounded-lg bg-primary text-white px-4 py-2 text-sm hover:opacity-90 disabled:opacity-60">
          {calcMutation.isPending ? '测算中…' : '重新测算'}
        </button>
        <button onClick={exportExcel} className="rounded-lg border border-card-border bg-card text-ink px-4 py-2 text-sm hover:bg-bg">
          导出 Excel
        </button>
      </div>

      {/* 表格 */}
      <div className="bg-card border border-card-border rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-bg/60 text-sub text-left">
            <tr>
              <th className="px-4 py-3 font-medium">SKU</th>
              <th className="px-4 py-3 font-medium">品名</th>
              <th className="px-4 py-3 font-medium">平台</th>
              <th className="px-4 py-3 font-medium">预测日销</th>
              <th className="px-4 py-3 font-medium">可售天数</th>
              <th className="px-4 py-3 font-medium">建议备货量</th>
              <th className="px-4 py-3 font-medium">评分</th>
              <th className="px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-card-border">
            {rows?.map((r) => (
              <tr key={r.sku} className="hover:bg-bg/40 cursor-pointer" onClick={() => setSelected(r)}>
                <td className="px-4 py-3 font-medium text-ink">{r.sku}</td>
                <td className="px-4 py-3 text-ink">
                  {r.name}
                  {r.is_adjusted && <span className="ml-2 text-xs text-primary">已调整</span>}
                  {r.is_ignored && <span className="ml-2 text-xs text-sub">已忽略</span>}
                </td>
                <td className="px-4 py-3 text-sub">{r.platform}</td>
                <td className="px-4 py-3 text-ink">{r.forecast_daily.toFixed(1)}</td>
                <td className={`px-4 py-3 ${r.sellable_days < 15 ? 'text-danger font-semibold' : 'text-ink'}`}>
                  {r.sellable_days < 999 ? r.sellable_days.toFixed(1) : '—'}
                </td>
                <td className="px-4 py-3 text-ink">{r.effective_qty}</td>
                <td className="px-4 py-3"><ScoreBadge score={r.score} /></td>
                <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                  <button onClick={() => ignore(r.sku)} className="text-xs text-sub hover:text-danger">忽略</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <div className="p-6 text-sub">加载中…</div>}
      </div>

      {/* 抽屉：评分依据 */}
      {selected && (
        <div className="fixed inset-0 z-50" onClick={() => setSelected(null)}>
          <div className="absolute inset-0 bg-black/30" />
          <div className="absolute right-0 top-0 h-full w-96 bg-card shadow-xl p-6 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-ink">{selected.sku} {selected.name}</h3>
              <button onClick={() => setSelected(null)} className="text-sub hover:text-ink">✕</button>
            </div>
            <div className="mb-4">
              <div className="text-sm text-sub mb-2">评分 {selected.score}（{selected.score_band}）</div>
              {Object.entries(selected.score_detail).map(([k, v]) => (
                <div key={k} className="mb-3">
                  <div className="flex justify-between text-xs text-sub mb-1">
                    <span>{k}</span>
                    <span>{v.score}/{v.max}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-bg">
                    <div className="h-1.5 rounded-full bg-primary" style={{ width: `${(v.score / v.max) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mb-4">
              <div className="text-sm text-sub mb-1">测算依据</div>
              <p className="text-sm text-ink leading-relaxed">{selected.reason_text || '—'}</p>
            </div>
            <div className="border-t border-card-border pt-4">
              <div className="text-sm text-sub mb-2">人工改量</div>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={adjustQty}
                  onChange={(e) => setAdjustQty(e.target.value)}
                  placeholder="输入新备货量"
                  className="flex-1 rounded-lg border border-card-border px-3 py-2 text-sm"
                />
                <button
                  onClick={() => adjustQty && updateMutation.mutate({ sku: selected.sku, qty: Number(adjustQty) })}
                  className="rounded-lg bg-primary text-white px-4 py-2 text-sm hover:opacity-90"
                >
                  保存
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
