export default function CategoryBars({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-ink/50">No spending logged yet.</p>
  }
  const max = Math.max(...data.map((d) => d.amount))

  return (
    <div className="space-y-3">
      {data.map((d) => (
        <div key={d.category} className="flex items-center gap-3">
          <div className="w-32 text-sm text-ink/70 truncate">{d.category}</div>
          <div className="flex-1 h-2 bg-line rounded overflow-hidden">
            <div
              className="h-full bg-indigo rounded"
              style={{ width: `${(d.amount / max) * 100}%` }}
            />
          </div>
          <div className="w-20 text-right font-nums text-sm text-ink">
            {d.amount.toFixed(0)}
          </div>
        </div>
      ))}
    </div>
  )
}
