import { useEffect, useState, useCallback } from 'react'
import api from '../api'
import Sidebar from '../components/Sidebar.jsx'
import BudgetForm from '../components/BudgetForm.jsx'
import BudgetChart from '../components/BudgetChart.jsx'

function currentMonth() {
  return new Date().toISOString().slice(0, 7) // 'YYYY-MM'
}

export default function Budgets() {
  const [month] = useState(currentMonth())
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    const res = await api.get('/budgets/vs-actual', { params: { month } })
    setData(res.data)
    setLoading(false)
  }, [month])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="flex min-h-screen bg-ivory">
      <Sidebar />
      <main className="flex-1 px-8 py-8 max-w-3xl">
        <header className="mb-8">
          <div className="text-xs uppercase tracking-wide text-ink/50">{month}</div>
          <h2 className="font-display text-3xl text-ink">Budgets</h2>
        </header>

        <section className="mb-8">
          <h3 className="text-sm uppercase tracking-wide text-ink/50 mb-3">Budget vs. actual</h3>
          {loading ? <p className="text-ink/50">Loading…</p> : <BudgetChart data={data} />}
        </section>

        <section>
          <h3 className="text-sm uppercase tracking-wide text-ink/50 mb-3">Set a monthly limit</h3>
          <BudgetForm month={month} onSaved={load} />
        </section>
      </main>
    </div>
  )
}
