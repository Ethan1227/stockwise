import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  arriveOrder,
  confirmOrder,
  deleteOrder,
  generateOrders,
  listOrders,
  shipOrder,
} from '../../api/purchase'

const STATUS_STYLE: Record<string, string> = {
  draft: 'bg-warning text-white',
  confirmed: 'bg-success text-white',
  shipped: 'bg-info text-white',
  arrived: 'bg-sub text-white',
}

const STATUS_LABEL: Record<string, string> = {
  draft: '待确认',
  confirmed: '已确认',
  shipped: '已发货',
  arrived: '已到货',
}

export function Purchase() {
  const queryClient = useQueryClient()
  const [skus, setSkus] = useState('')
  const [status, setStatus] = useState('')

  const { data: orders } = useQuery({
    queryKey: ['purchase-orders', status],
    queryFn: () => listOrders({ status: status || undefined }),
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['purchase-orders'] })

  const generateMutation = useMutation({
    mutationFn: generateOrders,
    onSuccess: () => {
      setSkus('')
      invalidate()
    },
  })
  const actionMutation = useMutation({
    mutationFn: ({ fn, id }: { fn: (id: number) => Promise<unknown>; id: number }) => fn(id),
    onSuccess: invalidate,
  })

  function onGenerate() {
    const list = skus.split(/[,，\s]+/).map((s) => s.trim()).filter(Boolean)
    if (list.length) generateMutation.mutate(list)
  }

  const totalAmount = orders?.reduce((s, o) => s + o.total_amount, 0) ?? 0

  return (
    <div className="space-y-5">
      {/* 生成区 */}
      <div className="bg-card border border-card-border rounded-xl p-5 flex flex-wrap items-center gap-3">
        <input
          value={skus}
          onChange={(e) => setSkus(e.target.value)}
          placeholder="输入 SKU（逗号分隔），如 SK-1023,SK-2087"
          className="flex-1 min-w-60 rounded-lg border border-card-border px-3 py-2 text-sm"
        />
        <button onClick={onGenerate} disabled={generateMutation.isPending} className="rounded-lg bg-primary text-white px-4 py-2 text-sm hover:opacity-90 disabled:opacity-60">
          {generateMutation.isPending ? '生成中…' : '从建议生成'}
        </button>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="rounded-lg border border-card-border bg-card px-3 py-2 text-sm">
          <option value="">全部状态</option>
          {Object.entries(STATUS_LABEL).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {/* 采购单卡片 */}
      <div className="space-y-4">
        {orders?.map((o) => (
          <div key={o.id} className="bg-card border border-card-border rounded-xl p-5 border-l-4" style={{ borderLeftColor: '#6366F1' }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-ink">{o.po_no}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full text-white ${STATUS_STYLE[o.status] ?? 'bg-sub'}`}>{STATUS_LABEL[o.status] ?? o.status}</span>
                {o.suggest_air && <span className="text-xs px-2 py-0.5 rounded-full bg-danger/10 text-danger">建议空运</span>}
              </div>
              <span className="text-sm text-sub">{o.supplier} · {o.dest_warehouse}</span>
            </div>

            <table className="w-full text-sm mb-3">
              <thead className="text-sub text-left">
                <tr>
                  <th className="py-1 font-medium">SKU</th>
                  <th className="py-1 font-medium">品名</th>
                  <th className="py-1 font-medium">数量</th>
                  <th className="py-1 font-medium">单价</th>
                  <th className="py-1 font-medium">金额</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-card-border">
                {o.items.map((it) => (
                  <tr key={it.sku}>
                    <td className="py-1.5 text-ink">{it.sku}</td>
                    <td className="py-1.5 text-sub">{it.name}</td>
                    <td className="py-1.5 text-ink">{it.qty}</td>
                    <td className="py-1.5 text-sub">{it.unit_cost}</td>
                    <td className="py-1.5 text-ink">{it.amount}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {Object.values(o.warning).length > 0 && (
              <div className="mb-3 rounded-lg bg-warning/10 text-warning text-xs px-3 py-2">
                {Object.values(o.warning).join('；')}
              </div>
            )}

            <div className="flex items-center justify-between">
              <span className="text-sm text-sub">小计 ¥{o.total_amount} / {o.total_qty} 件</span>
              <div className="flex gap-2">
                {o.status === 'draft' && (
                  <>
                    <button onClick={() => actionMutation.mutate({ fn: confirmOrder, id: o.id })} className="text-xs rounded-lg bg-success/10 text-success px-3 py-1.5 hover:bg-success/20">确认下单</button>
                    <button onClick={() => actionMutation.mutate({ fn: deleteOrder, id: o.id })} className="text-xs rounded-lg bg-sub/10 text-sub px-3 py-1.5 hover:bg-sub/20">删除</button>
                  </>
                )}
                {o.status === 'confirmed' && (
                  <button onClick={() => actionMutation.mutate({ fn: shipOrder, id: o.id })} className="text-xs rounded-lg bg-info/10 text-info px-3 py-1.5 hover:bg-info/20">发货</button>
                )}
                {o.status === 'shipped' && (
                  <button onClick={() => actionMutation.mutate({ fn: arriveOrder, id: o.id })} className="text-xs rounded-lg bg-primary/10 text-primary px-3 py-1.5 hover:bg-primary/20">到货</button>
                )}
              </div>
            </div>
          </div>
        ))}
        {orders && orders.length === 0 && <div className="text-sub text-sm p-6 bg-card border border-card-border rounded-xl">暂无采购单</div>}
      </div>

      {/* 汇总 */}
      <div className="bg-card border border-card-border rounded-xl p-5">
        <div className="flex justify-between text-sm text-sub mb-2">
          <span>采购单 {orders?.length ?? 0} 张 · 总金额 ¥{totalAmount.toFixed(2)}</span>
          <span>月预算 ¥140000</span>
        </div>
        <div className="h-2 rounded-full bg-bg">
          <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.min(100, (totalAmount / 140000) * 100)}%` }} />
        </div>
      </div>
    </div>
  )
}
