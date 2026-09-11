import { request } from './client'

export interface FeatureFlags {
  datacenter: boolean
  engine: boolean
  suggestion: boolean
  alert: boolean
  purchase: boolean
  dashboard: boolean
  chat: boolean
  settings: boolean
}

export function getFlags() {
  return request<FeatureFlags>('/api/settings/flags')
}

export function updateFlags(flags: Partial<FeatureFlags>) {
  return request<FeatureFlags>('/api/settings/flags', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(flags),
  })
}
