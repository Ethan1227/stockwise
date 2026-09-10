import { request } from './client'

export interface Sku {
  sku: string
  name: string
  platform: string
  category: string
  supplier: string
  unit_cost: number
  price: number
  moq: number
  lead_prod_days: number
  lead_ship_days: number
  safety_days: number
}

export function listSkus() {
  return request<Sku[]>('/api/skus')
}

export function createSku(body: Partial<Sku>) {
  return request<Sku>('/api/skus', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function updateSku(sku: string, body: Partial<Sku>) {
  return request<Sku>(`/api/skus/${sku}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function deleteSku(sku: string) {
  return request(`/api/skus/${sku}`, { method: 'DELETE' })
}
