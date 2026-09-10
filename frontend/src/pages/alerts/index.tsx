import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getRules, listAlerts, updateAlert, updateRules } from '../../api/alerts'

const LEVEL_STYLE: Record<string, string> = {
  紧急: 'bg-danger text-white',
  严重: 'bg-danger text-white',
  一般: 'bg-warning text-white',
  轻度: 'bg-info text-white',
}

const TYPE_STYLE: Record<string, string> = {
  缺货: 'bg-danger',
  滞销: 'bg-warning',
}

const RULE_LABELS: Record<string, string> = {
  stockout_urgent_days: '缺货紧急（可售天数 < X）',
  stockout_normal_days: '缺货一般（可售天数 < X）',
  slow_severe_turnover: '滞销严重（周转 > X 天）',
  slow_severe_age: '滞销严重（库龄 > X 天）',
  slow_mild_turnover: '滞销轻度（周转 > X 天）',
}

export function Alerts() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [type, setType] = useState('')
  const [rules, setRules] = useState<Record<string, number>>({})
  const [rulesDirty, setRulesDirty] = useState(false)

  const { data: alerts } = useQuery({
    queryKey: ['alerts', type],
    queryFn: () => listAlerts({ type: type || undefined }),
  })

  const { data: rulesData } = useQuery({
    queryKey: ['rules'],
    queryFn: getRules,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => updateAlert(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const rulesMutation = useMutation({
    mutationFn: updateRules,
    onSuccess: () => {
      setRulesDirty(false)
      queryClient.invalidateQueries({ queryKey: ['rules'] })
    },
  })

  const total = alerts?.length ?? 0
  const stockoutCount = alerts?.filter((a) => a.alert_type === '缺货').length ?? 0
  const slowCount = alerts?.filter((a) => a.alert_type === '滞销').length ?? 0

  function editRule(key: string, value: string) {
    setRules({ ...rules, [key]: Number(value) })
    setRulesDirty(true)
  }

  return (
    <div className="space-y-6">
      {/* Tab 徽章 */}
      <div className="flex gap-2">
        {[
          { label: '全部', value: '', count: total },
          { label: '缺货', value: '缺货', count: stockoutCount },
          { label: '滞销', value: '滞销', count: slowCount },
        ].map((t) => (
          <button
            key={t.value}
            onClick={() => setType(t.value)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium ${
              type === t.value ? 'bg-primary text-white' : 'bg-card border border-card-border text-ink'
            }`}
          >
            {t.label} {t.count}
          </button>
        ))}
      </div>

      {/* 预警卡片 */}
      <div className="space-y-3">
        {alerts?.map((a) => (
          <div key={a.id} className="bg-card border border-card-border rounded-xl p-4 flex gap-4 border-l-4" style={{ borderLeftColor: TYPE_STYLE[a.alert_type] ?? '#3B82F6' }}>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs px-2 py-0.5 rounded-full text-white ${LEVEL_STYLE[a.level] ?? 'bg-sub'}`}>{a.level}</span>
                <span className="font-semibold text-ink">{a.title}</span>
                <span className="text-xs text-sub">{a.sku}</span>
              </div>
              <p className="text-sm text-sub mb-1">{a.detail}</p>
              <p className="text-sm text-ink">{a.advice}</p>
            </div>
            <div className="flex flex-col gap-2 justify-center">
              {a.status === '未处理' ? (
                <>
                  {a.alert_type === '缺货' && (
                    <button onClick={() => navigate(`/purchase?skus=${a.sku}`)} className="text-xs rounded-lg bg-primary text-white px-3 py-1.5 hover:opacity-90">
                      生成采购单
                    </button>
                  )}
                  <button onClick={() => updateMutation.mutate({ id: a.id, status: '已处理' })} className="text-xs rounded-lg bg-primary/10 text-primary px-3 py-1.5 hover:bg-primary/20">
                    标记处理
                  </button>
                  <button onClick={() => updateMutation.mutate({ id: a.id, status: '已忽略' })} className="text-xs rounded-lg bg-sub/10 text-sub px-3 py-1.5 hover:bg-sub/20">
                    忽略
                  </button>
                </>
              ) : (
                <span className="text-xs text-sub">{a.status}</span>
              )}
            </div>
          </div>
        ))}
        {alerts && alerts.length === 0 && <div className="text-sub text-sm p-6">暂无预警</div>}
      </div>

      {/* 规则配置 */}
      <div className="bg-card border border-card-border rounded-xl p-5">
        <h3 className="font-semibold text-ink mb-4">预警规则配置</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Object.entries(rulesData ?? {}).map(([key, val]) => (
            <div key={key} className="flex items-center justify-between gap-3">
              <span className="text-sm text-ink">{RULE_LABELS[key] ?? key}</span>
              <input
                type="number"
                defaultValue={val}
                onChange={(e) => editRule(key, e.target.value)}
                className="w-24 rounded-lg border border-card-border px-3 py-1.5 text-sm"
              />
            </div>
          ))}
        </div>
        <button
          onClick={() => rulesMutation.mutate(rules)}
          disabled={!rulesDirty}
          className="mt-4 rounded-lg bg-primary text-white px-4 py-2 text-sm hover:opacity-90 disabled:opacity-50"
        >
          保存规则
        </button>
      </div>
    </div>
  )
}
