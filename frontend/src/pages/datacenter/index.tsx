import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { importCsv, ImportError, listDatasources } from '../../api/datasources'

interface ImportFeedback {
  source: string
  written: number
  errors: ImportError[]
}

export function DataCenter() {
  const queryClient = useQueryClient()
  const { data: sources, isLoading } = useQuery({ queryKey: ['datasources'], queryFn: listDatasources })
  const [feedback, setFeedback] = useState<ImportFeedback | null>(null)

  const importMutation = useMutation({
    mutationFn: ({ source, file }: { source: string; file: File }) => importCsv(source, file),
    onSuccess: (data, vars) => {
      setFeedback({ source: vars.source, written: data.written, errors: data.errors })
      queryClient.invalidateQueries({ queryKey: ['datasources'] })
    },
    onError: (err: Error) => setFeedback({ source: '', written: 0, errors: [{ row: 0, message: err.message }] }),
  })

  function onFileChange(source: string, file: File | undefined) {
    if (file) importMutation.mutate({ source, file })
  }

  if (isLoading) return <div className="text-sub">加载中…</div>

  const hasError = feedback ? feedback.errors.length > 0 : false

  return (
    <div>
      {feedback && (
        <div
          className={`mb-4 rounded-lg px-4 py-3 text-sm border ${
            hasError
              ? 'bg-danger/10 border-danger/30 text-danger'
              : 'bg-success/10 border-success/30 text-success'
          }`}
        >
          {feedback.source} 导入完成：写入 {feedback.written} 行
          {hasError &&
            `，错误 ${feedback.errors.length} 条：${feedback.errors
              .slice(0, 3)
              .map((e) => `第${e.row}行 ${e.message}`)
              .join('；')}`}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {sources?.map((s) => (
          <div key={s.source_code} className="bg-card border border-card-border rounded-xl p-5">
            <div className="flex items-center justify-between mb-1">
              <h3 className="font-semibold text-ink">{s.name}</h3>
              <span
                className={`inline-flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full ${
                  s.status === '已连接' ? 'bg-success/10 text-success' : 'bg-sub/10 text-sub'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${s.status === '已连接' ? 'bg-success' : 'bg-sub'}`} />
                {s.status}
              </span>
            </div>
            <p className="text-xs text-sub mb-4">上次同步：{s.last_sync ?? '—'}</p>
            <label className="inline-block cursor-pointer rounded-lg bg-primary text-white text-sm px-4 py-2 hover:opacity-90">
              {importMutation.isPending ? '导入中…' : '上传 CSV'}
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => onFileChange(s.source_code, e.target.files?.[0])}
              />
            </label>
          </div>
        ))}
      </div>
    </div>
  )
}
