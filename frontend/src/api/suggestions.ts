import { request } from './client'

export interface ScoreDetail {
  score: number
  max: number
}

export interface Suggestion {
  sku: string
  name: string
  platform: string
  category: string
  supplier: string
  fba_qty: number
  wfs_qty: number
  cn_qty: number
  in_transit_qty: number
  forecast_daily: number
  sellable_days: number
  suggest_qty: number
  score: number
  score_band: string
  score_detail: Record<string, ScoreDetail>
  reason_text: string
  adjusted_qty: number | null
  is_adjusted: boolean
  is_ignored: boolean
  effective_qty: number
}

export function listSuggestions(params?: { platform?: string; score_band?: string; status?: string }) {
  const q = new URLSearchParams()
  if (params?.platform) q.set('platform', params.platform)
  if (params?.score_band) q.set('score_band', params.score_band)
  if (params?.status) q.set('status', params.status)
  const qs = q.toString()
  return request<Suggestion[]>(`/api/suggestions${qs ? `?${qs}` : ''}`)
}

export function updateSuggestion(sku: string, body: { adjusted_qty: number | null; note?: string }) {
  return request(`/api/suggestions/${sku}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function triggerCalc() {
  return request<{ calc_date: string; count: number }>('/api/calc/run', { method: 'POST' })
}
