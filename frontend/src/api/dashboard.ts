import { request } from './client'

export interface Kpi {
  sku_count: number
  suggest_count: number
  stockout: number
  stockout_urgent: number
  slow: number
}
export interface DataSourceStatus {
  source_code: string
  name: string
  last_sync: string | null
  status: string
}
export interface SalesPoint {
  date: string
  amazon: number
  walmart: number
}
export interface Todo {
  type: string
  text: string
  route: string
}
export interface Summary {
  kpi: Kpi
  datasources: DataSourceStatus[]
  sales_series: SalesPoint[]
  todos: Todo[]
}

export function getSummary() {
  return request<Summary>('/api/dashboard/summary')
}
