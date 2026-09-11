import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { FeatureFlags } from '../api/flags'
import { getFlags, updateFlags } from '../api/flags'
import { getEvalDocs, getEvalMetrics, getRagas } from '../api/eval'

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

const METRIC_LABELS: Record<string, string> = {
  intent: '意图识别',
  stockout: '断货预警',
  slow: '滞销预警',
  score_band: '评分档',
  suggest: '建议量',
}

const RAGAS_LABELS: Record<string, string> = {
  faithfulness: '忠实度',
  answer_relevancy: '答案相关性',
  context_precision: '上下文精确率',
  context_recall: '上下文召回率',
}

export function TestConfigCenter({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [docOpen, setDocOpen] = useState(false)

  const { data: flags } = useQuery({ queryKey: ['flags'], queryFn: getFlags, enabled: open })
  const { data: metrics } = useQuery({ queryKey: ['eval-metrics'], queryFn: getEvalMetrics, enabled: open })
  const { data: ragas } = useQuery({ queryKey: ['eval-ragas'], queryFn: getRagas, enabled: open })
  const { data: docs } = useQuery({ queryKey: ['eval-docs'], queryFn: getEvalDocs, enabled: open })

  const flagMutation = useMutation({
    mutationFn: updateFlags,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['flags'] }),
  })

  if (!open) return null

  function toggle(key: keyof FeatureFlags, value: boolean) {
    flagMutation.mutate({ [key]: value })
  }

  const barData = Object.entries(metrics ?? {}).map(([k, v]) => ({ name: METRIC_LABELS[k] ?? k, F1: v.f1 }))
  const radarData = Object.entries(ragas ?? {}).map(([k, v]) => ({ metric: RAGAS_LABELS[k] ?? k, value: v }))

  return (
    <div className="fixed inset-0 z-50 bg-bg overflow-y-auto" onClick={onClose}>
      <div className="max-w-4xl mx-auto p-4 md:p-8" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-ink">测试配置中心</h2>
          <button onClick={onClose} className="text-sub hover:text-ink">✕ 关闭</button>
        </div>

        {/* 权限分配 */}
        <section className="bg-card border border-card-border rounded-xl p-5 mb-5">
          <h3 className="font-semibold text-ink mb-3">权限分配（功能开关）</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
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
                    <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${on ? 'translate-x-5' : 'translate-x-0.5'}`} />
                  </button>
                </div>
              )
            })}
          </div>
        </section>

        {/* 评测报告 */}
        <section className="bg-card border border-card-border rounded-xl p-5 mb-5">
          <h3 className="font-semibold text-ink mb-4">评测报告</h3>
          <h4 className="text-sm text-sub mb-2">传统指标（准确率 / 精确率 / 召回率 / F1）</h4>
          <div className="overflow-x-auto mb-4">
            <table className="w-full text-sm min-w-[480px]">
              <thead className="text-sub text-left">
                <tr>
                  <th className="py-2 font-medium">功能</th>
                  <th className="py-2 font-medium">准确率</th>
                  <th className="py-2 font-medium">精确率</th>
                  <th className="py-2 font-medium">召回率</th>
                  <th className="py-2 font-medium">F1</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-card-border">
                {Object.entries(metrics ?? {}).map(([k, v]) => (
                  <tr key={k}>
                    <td className="py-2 text-ink">{METRIC_LABELS[k] ?? k}</td>
                    <td className="py-2 text-ink">{(v.accuracy * 100).toFixed(1)}%</td>
                    <td className="py-2 text-ink">{(v.precision * 100).toFixed(1)}%</td>
                    <td className="py-2 text-ink">{(v.recall * 100).toFixed(1)}%</td>
                    <td className="py-2 text-ink">{(v.f1 * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="h-56 mb-5">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E6E9F2" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#8A90A6' }} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 11, fill: '#8A90A6' }} />
                <Tooltip />
                <Bar dataKey="F1" fill="#6366F1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <h4 className="text-sm text-sub mb-2">RAGAS 指标</h4>
          <div className="overflow-x-auto mb-4">
            <table className="w-full text-sm min-w-[320px]">
              <thead className="text-sub text-left">
                <tr>
                  <th className="py-2 font-medium">指标</th>
                  <th className="py-2 font-medium">分值</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-card-border">
                {Object.entries(ragas ?? {}).map(([k, v]) => (
                  <tr key={k}>
                    <td className="py-2 text-ink">{RAGAS_LABELS[k] ?? k}</td>
                    <td className="py-2 text-ink">{(v * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} outerRadius="70%">
                <PolarGrid stroke="#E6E9F2" />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12, fill: '#8A90A6' }} />
                <PolarRadiusAxis domain={[0, 1]} tick={{ fontSize: 10, fill: '#8A90A6' }} />
                <Radar dataKey="value" stroke="#6366F1" fill="#6366F1" fillOpacity={0.4} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* 测试说明文档 */}
        <section className="bg-card border border-card-border rounded-xl p-5">
          <h3 className="font-semibold text-ink mb-2">测试说明文档</h3>
          <p className="text-sm text-sub mb-3">包含评测数据集、QA 测试对与预期结果。</p>
          <div className="flex gap-3">
            <button onClick={() => setDocOpen(true)} className="rounded-lg bg-primary text-white px-4 py-2 text-sm hover:opacity-90">
              打开测试说明文档
            </button>
            <button onClick={() => navigate('/chat')} className="rounded-lg border border-card-border bg-card text-ink px-4 py-2 text-sm hover:bg-bg">
              跳转测试页（AI 问答）
            </button>
          </div>
        </section>
      </div>

      {docOpen && <DocModal markdown={docs?.markdown ?? ''} onClose={() => setDocOpen(false)} navigate={navigate} />}
    </div>
  )
}

function DocModal({ markdown, onClose, navigate }: { markdown: string; onClose: () => void; navigate: (p: string) => void }) {
  const [copied, setCopied] = useState(false)

  function copyAll() {
    navigator.clipboard.writeText(markdown)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  function jumpToTest() {
    const q = markdown.match(/本周要补什么货？/)?.[0] ?? '本周要补什么货？'
    navigate(`/chat?q=${encodeURIComponent(q)}`)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40" />
      <div className="relative bg-card rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-card-border">
          <h3 className="font-semibold text-ink">测试说明文档</h3>
          <div className="flex gap-2">
            <button onClick={copyAll} className="text-xs rounded-lg bg-primary/10 text-primary px-3 py-1.5">
              {copied ? '已复制' : '一键复制全文'}
            </button>
            <button onClick={jumpToTest} className="text-xs rounded-lg bg-primary text-white px-3 py-1.5">
              跳转测试
            </button>
            <button onClick={onClose} className="text-sub hover:text-ink">✕</button>
          </div>
        </div>
        <div className="p-4 overflow-y-auto whitespace-pre-wrap text-sm text-ink leading-relaxed">{markdown}</div>
      </div>
    </div>
  )
}
