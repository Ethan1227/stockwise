import { request } from './client'

export interface DataSource {
  source_code: string
  name: string
  last_sync: string | null
  status: string
}

export interface ImportError {
  row: number
  message: string
}

export interface ImportResult {
  source: string
  total: number
  written: number
  errors: ImportError[]
}

export function listDatasources() {
  return request<DataSource[]>('/api/datasources')
}

export function importCsv(source: string, file: File) {
  const form = new FormData()
  form.append('file', file)
  return request<ImportResult>(`/api/import/${source}`, { method: 'POST', body: form })
}
