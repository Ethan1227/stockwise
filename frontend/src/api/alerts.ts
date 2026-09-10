import { request } from './client'

export interface Alert {
  id: number
  sku: string
  code: string
  alert_type: string
  level: string
  title: string
  detail: string
  advice: string
  status: string
  notify_log: Record<string, unknown>
  created_at: string | null
}

export function listAlerts(params?: { type?: string; level?: string; status?: string }) {
  const q = new URLSearchParams()
  if (params?.type) q.set('type', params.type)
  if (params?.level) q.set('level', params.level)
  if (params?.status) q.set('status', params.status)
  const qs = q.toString()
  return request<Alert[]>(`/api/alerts${qs ? `?${qs}` : ''}`)
}

export function updateAlert(id: number, status: string) {
  return request(`/api/alerts/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
}

export function getRules() {
  return request<Record<string, number>>('/api/settings/rules')
}

export function updateRules(rules: Record<string, number>) {
  return request<Record<string, number>>('/api/settings/rules', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rules),
  })
}
