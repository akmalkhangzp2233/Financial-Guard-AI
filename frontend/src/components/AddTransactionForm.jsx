import { useState } from 'react'
import api from '../api'
import CategorySelect from './CategorySelect.jsx'

export default function AddTransactionForm({ onAdded }) {
  const [amount, setAmount] = useState('')
  const [merchant, setMerchant] = useState('')
  const [categoryId, setCategoryId] = useState(null)
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api.post('/transactions/', {
        amount: parseFloat(amount),
        merchant,
        category_id: parseInt(categoryId),
        txn_date: date,
      })
      setAmount('')
      setMerchant('')
      onAdded?.()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 border border-line bg-white rounded px-4 py-3">
      <div>
        <label className="text-xs uppercase tracking-wide text-ink/50 block">Amount</label>
        <input required type="number" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)}
          className="w-28 border border-line px-2 py-1 rounded font-nums" />
      </div>
      <div>
        <label className="text-xs uppercase tracking-wide text-ink/50 block">Merchant</label>
        <input value={merchant} onChange={(e) => setMerchant(e.target.value)}
          className="w-40 border border-line px-2 py-1 rounded" />
      </div>
      <div>
        <label className="text-xs uppercase tracking-wide text-ink/50 block">Category</label>
        <CategorySelect value={categoryId} onChange={setCategoryId} />
      </div>
      <div>
        <label className="text-xs uppercase tracking-wide text-ink/50 block">Date</label>
        <input required type="date" value={date} onChange={(e) => setDate(e.target.value)}
          className="border border-line px-2 py-1 rounded" />
      </div>
      <button disabled={submitting || !categoryId} type="submit" className="bg-ink text-white px-4 py-1.5 rounded text-sm hover:bg-ink/80 disabled:opacity-50">
        {submitting ? 'Adding…' : 'Add entry'}
      </button>
    </form>
  )
}
