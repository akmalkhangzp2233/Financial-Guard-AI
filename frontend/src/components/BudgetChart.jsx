export default function BudgetChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-sm text-ink/50">No budgets set for this month yet.</p>
  }

  return (
    <div className="space-y-4">
      {data.map((b) => {
        const pct = Math.min((b.spent / b.limit) * 100, 100)
        const over = b.spent > b.limit
        return (
          <div key={b.category_id}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-ink/70">{b.category_name}</span>
              <span className={`font-nums ${over ? 'text-alert' : 'text-ink'}`}>
                {b.spent.toFixed(0)} / {b.limit.toFixed(0)}
              </span>
            </div>
            <div className="h-2 bg-line rounded overflow-hidden">
              <div
                className={`h-full rounded ${over ? 'bg-alert' : 'bg-indigo'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
