import { request } from './client'

export interface PurchaseItem {
  sku: string
  name: string
  qty: number
  unit_cost: number
  amount: number
}

export interface PurchaseOrder {
  id: number
  po_no: string
  supplier: string
  status: string
  total_qty: number
  total_amount: number
  dest_warehouse: string
  items: PurchaseItem[]
  suggest_air: boolean
  warning: Record<string, string>
  created_at: string | null
}

export function listOrders(params?: { status?: string }) {
  const q = new URLSearchParams()
  if (params?.status) q.set('status', params.status)
  const qs = q.toString()
  return request<PurchaseOrder[]>(`/api/purchase-orders${qs ? `?${qs}` : ''}`)
}

export function generateOrders(skus: string[]) {
  return request<PurchaseOrder[]>('/api/purchase-orders/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skus }),
  })
}

export function confirmOrder(id: number) {
  return request(`/api/purchase-orders/${id}/confirm`, { method: 'PUT' })
}
export function shipOrder(id: number) {
  return request(`/api/purchase-orders/${id}/ship`, { method: 'PUT' })
}
export function arriveOrder(id: number) {
  return request(`/api/purchase-orders/${id}/arrive`, { method: 'PUT' })
}
export function deleteOrder(id: number) {
  return request(`/api/purchase-orders/${id}`, { method: 'DELETE' })
}

export function createManualOrder(body: {
  supplier: string
  dest_warehouse: string
  status: string
  items: { sku: string; qty: number; unit_cost: number }[]
}) {
  return request<PurchaseOrder>('/api/purchase-orders/manual', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
