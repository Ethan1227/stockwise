import { request } from './client'

export interface ChatChip {
  label: string
  value: string
}
export interface ChatAction {
  type: string
  label?: string
  route?: string
}
export interface ThinkingStep {
  step: string
  detail: string
}
export interface ChatResponse {
  answer_md: string
  data_chips: ChatChip[]
  actions: ChatAction[]
  suggestions: string[]
  llm?: string
}

export function sendChat(text: string) {
  return request<ChatResponse>('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
}

export interface StreamHandlers {
  onThinking: (steps: ThinkingStep[]) => void
  onToken: (token: string) => void
  onMeta: (meta: { data_chips: ChatChip[]; actions: ChatAction[] }) => void
  onLlm: (model: string) => void
  onDone: () => void
  onError: () => void
}

// SSE 流式问答：解析 text/event-stream，逐事件回调
export function streamChat(text: string, handlers: StreamHandlers): () => void {
  const controller = new AbortController()
  ;(async () => {
    let completed = false
    const finish = () => {
      if (!completed) {
        completed = true
        handlers.onDone()
      }
    }
    try {
      const resp = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
        signal: controller.signal,
      })
      if (!resp.ok || !resp.body) {
        handlers.onError()
        finish()
        return
      }
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() ?? ''
        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'thinking') handlers.onThinking(data.content)
            else if (data.type === 'token') handlers.onToken(data.content)
            else if (data.type === 'meta') handlers.onMeta(data.content)
            else if (data.type === 'llm') handlers.onLlm(data.content)
            else if (data.type === 'done') finish()
          } catch {
            /* 忽略单条解析错误 */
          }
        }
      }
      finish()
    } catch {
      handlers.onError()
      finish()
    }
  })()
  return () => controller.abort()
}
