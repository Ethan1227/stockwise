import { request } from './client'

export interface EvalMetrics {
  accuracy: number
  precision: number
  recall: number
  f1: number
  samples: number
}

export interface RagasMetrics {
  faithfulness: number
  answer_relevancy: number
  context_precision: number
  context_recall: number
}

export function getEvalMetrics() {
  return request<Record<string, EvalMetrics>>('/api/eval/metrics')
}

export function getRagas() {
  return request<RagasMetrics>('/api/eval/ragas')
}

export function getEvalDocs() {
  return request<{ markdown: string }>('/api/eval/docs')
}
