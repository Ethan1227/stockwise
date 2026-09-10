import { request } from './client'

export interface PromotionEvent {
  event: string
  event_date: string
  warehouse_deadline: string
}

export interface Settings {
  base_weights: { '30d': number; '90d': number; yoy: number }
  safety_days: number
  lead_transit_sea: number
  lead_transit_air: number
  lead_shelf_days: number
  monthly_budget: number
  alert_thresholds: Record<string, number>
  modifier_tiers: Record<string, Record<string, number>>
  promotion_calendar: PromotionEvent[]
}

export function getSettings() {
  return request<Settings>('/api/settings')
}

export function updateSettings(body: Record<string, unknown>) {
  return request<Settings>('/api/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
