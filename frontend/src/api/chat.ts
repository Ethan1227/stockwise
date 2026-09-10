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
export interface ChatResponse {
  answer_md: string
  data_chips: ChatChip[]
  actions: ChatAction[]
  suggestions: string[]
}

export function sendChat(text: string) {
  return request<ChatResponse>('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
}
