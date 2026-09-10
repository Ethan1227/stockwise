// 统一 fetch 封装：解析后端 {code, data, message}
export async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, init)
  if (!resp.ok) {
    const body = await resp.json().catch(() => null)
    throw new Error(body?.message || `HTTP ${resp.status}`)
  }
  const body = await resp.json()
  if (body.code !== 0) {
    throw new Error(body.message || '请求失败')
  }
  return body.data as T
}
