import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChatChip, sendChat } from '../../api/chat'

interface Message {
  role: 'user' | 'ai'
  text: string
  chips: ChatChip[]
  actions: { type: string; label?: string; route?: string }[]
}

const SUGGESTIONS = [
  '本周要补什么货？',
  'SK-2087 会断货吗？',
  '哪些产品滞销？',
  '黑五大促排期？',
]

export function Chat() {
  const navigate = useNavigate()
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])

  const chatMutation = useMutation({
    mutationFn: sendChat,
    onSuccess: (data, text) => {
      setMessages((m) => [
        ...m,
        { role: 'user', text, chips: [], actions: [] },
        { role: 'ai', text: data.answer_md, chips: data.data_chips, actions: data.actions },
      ])
    },
  })

  function send(text: string) {
    const t = text.trim()
    if (!t) return
    setInput('')
    chatMutation.mutate(t)
  }

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      {/* 消息区 */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.length === 0 && (
          <div className="text-center py-16">
            <h2 className="text-xl font-semibold text-ink mb-1">你好，管理员。今天想了解什么备货问题？</h2>
            <p className="text-sm text-sub mb-8">数据来自每日 06:30 自动测算</p>
            <div className="grid grid-cols-2 gap-3 max-w-md mx-auto">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-left rounded-xl bg-card border border-card-border p-4 text-sm text-ink hover:border-primary"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) =>
          m.role === 'user' ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[70%] rounded-xl rounded-br-sm bg-primary text-white px-4 py-2.5 text-sm">{m.text}</div>
            </div>
          ) : (
            <div key={i} className="flex justify-start">
              <div className="max-w-[80%] rounded-xl rounded-bl-sm bg-card border border-card-border px-4 py-3">
                <p className="text-sm text-ink whitespace-pre-line leading-relaxed">{m.text}</p>
                {m.chips.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {m.chips.map((c, j) => (
                      <span key={j} className="text-xs rounded-full bg-primary/10 text-primary px-2 py-0.5">
                        {c.label}: {c.value}
                      </span>
                    ))}
                  </div>
                )}
                {m.actions.length > 0 && (
                  <div className="flex gap-2 mt-2">
                    {m.actions.map((a, j) =>
                      a.type === 'link' ? (
                        <button
                          key={j}
                          onClick={() => a.route && navigate(a.route)}
                          className="text-xs rounded-lg bg-primary text-white px-3 py-1.5"
                        >
                          {a.label}
                        </button>
                      ) : (
                        <span key={j} className="text-xs rounded-lg bg-primary/10 text-primary px-3 py-1.5">{a.label ?? a.type}</span>
                      ),
                    )}
                  </div>
                )}
              </div>
            </div>
          ),
        )}
        {chatMutation.isPending && <div className="text-sm text-sub">思考中…</div>}
      </div>

      {/* 输入区 */}
      <div className="flex gap-2 pt-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send(input)}
          placeholder="输入你的问题…"
          className="flex-1 rounded-xl border border-card-border bg-card px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
        />
        <button
          onClick={() => send(input)}
          disabled={chatMutation.isPending}
          className="rounded-xl bg-primary text-white px-5 py-2.5 text-sm hover:opacity-90 disabled:opacity-60"
        >
          发送
        </button>
      </div>
    </div>
  )
}
