import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { FeatureFlags } from '../api/flags'
import { getFlags, updateFlags } from '../api/flags'

const FEATURES: { key: keyof FeatureFlags; label: string }[] = [
  { key: 'dashboard', label: '工作台总览' },
  { key: 'datacenter', label: '数据中心' },
  { key: 'engine', label: '测算引擎' },
  { key: 'suggestion', label: '备货建议' },
  { key: 'alert', label: '预警中心' },
  { key: 'purchase', label: '采购计划' },
  { key: 'chat', label: 'AI 问答' },
  { key: 'settings', label: '系统设置' },
]

export function TestConfigCenter({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { data: flags } = useQuery({ queryKey: ['flags'], queryFn: getFlags, enabled: open })
  const mutation = useMutation({
    mutationFn: updateFlags,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['flags'] }),
  })

  if (!open) return null

  function toggle(key: keyof FeatureFlags, value: boolean) {
    mutation.mutate({ [key]: value })
  }

  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <div className="absolute inset-0 bg-black/30" />
      <div
        className="absolute right-0 top-0 h-full w-full md:w-96 bg-card shadow-xl p-6 overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-semibold text-ink">测试配置中心</h3>
          <button onClick={onClose} className="text-sub hover:text-ink">✕</button>
        </div>

        <h4 className="text-sm font-medium text-ink mb-3">权限分配（功能开关）</h4>
        <div>
          {FEATURES.map((f) => {
            const on = flags?.[f.key] ?? true
            return (
              <div key={f.key} className="flex items-center justify-between py-2.5 border-b border-card-border">
                <span className="text-sm text-ink">{f.label}</span>
                <button
                  onClick={() => toggle(f.key, !on)}
                  aria-label={`开关 ${f.label}`}
                  className={`w-11 h-6 rounded-full relative transition-colors ${on ? 'bg-primary' : 'bg-sub/30'}`}
                >
                  <span
                    className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${on ? 'translate-x-5' : 'translate-x-0.5'}`}
                  />
                </button>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
