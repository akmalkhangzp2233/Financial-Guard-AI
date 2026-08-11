import { useState } from 'react'
import api from '../api'
import CategorySelect from './CategorySelect.jsx'

export default function BudgetForm({ month, onSaved }) {
  const [categoryId, setCategoryId] = useState(null)
  const [limit, setLimit] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api.post('/budgets/', {
        category_id: categoryId,
        month,
        limit_amount: parseFloat(limit),
      })
      setLimit('')
      onSaved?.()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 border border-line bg-white rounded px-4 py-3">
      <div>
        <label className="text-xs uppercase tracking-wide text-ink/50 block">Category</label>
        <CategorySelect value={categoryId} onChange={setCategoryId} incomeOnly={false} />
      </div>
      <div>
        <label className="text-xs uppercase tracking-wide text-ink/50 block">Monthly limit</label>
        <input required type="number" step="0.01" value={limit} onChange={(e) => setLimit(e.target.value)}
          className="w-28 border border-line px-2 py-1 rounded font-nums" />
      </div>
      <button disabled={submitting || !categoryId} type="submit" className="bg-ink text-white px-4 py-1.5 rounded text-sm hover:bg-ink/80 disabled:opacity-50">
        {submitting ? 'Saving…' : 'Set budget'}
      </button>
    </form>
  )
}
