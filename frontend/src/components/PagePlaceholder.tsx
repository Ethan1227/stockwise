export function PagePlaceholder({ title }: { title: string }) {
  return (
    <div className="bg-card border border-card-border rounded-xl p-6">
      <h2 className="text-xl font-semibold text-ink mb-2">{title}</h2>
      <p className="text-sub text-sm">该页面将在后续阶段开发。</p>
    </div>
  )
}
