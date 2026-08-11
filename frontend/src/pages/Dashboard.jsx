import { useEffect, useState, useCallback } from 'react'
import api from '../api'
import Sidebar from '../components/Sidebar.jsx'
import StatCard from '../components/StatCard.jsx'
import CategoryBars from '../components/CategoryBars.jsx'
import FraudAlerts from '../components/FraudAlerts.jsx'
import AddTransactionForm from '../components/AddTransactionForm.jsx'
import AIInsights from '../components/AIInsights.jsx'
import ScanReceipt from '../components/ScanReceipt.jsx'

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadAll = useCallback(async () => {
    setLoading(true)
    const [s, a, f] = await Promise.all([
      api.get('/insights/summary'),
      api.get('/insights/fraud-alerts'),
      api.get('/insights/forecast'),
    ])
    setSummary(s.data)
    setAlerts(a.data)
    setForecast(f.data)
    setLoading(false)
  }, [])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  return (
    <div className="flex min-h-screen bg-ivory">
      <Sidebar />

      <main className="flex-1 px-8 py-8 max-w-5xl">
        <header className="mb-8">
          <div className="text-xs uppercase tracking-wide text-ink/50">Overview</div>
          <h2 className="font-display text-3xl text-ink">This month's ledger</h2>
        </header>

        {loading && <p className="text-ink/50">Loading…</p>}

        {!loading && summary && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard label="Total spent" value={summary.total_spent.toFixed(2)} />
              <StatCard label="Total income" value={summary.total_income.toFixed(2)} accent="indigo" />
              <StatCard
                label="Net savings"
                value={summary.savings.toFixed(2)}
                accent={summary.savings >= 0 ? 'indigo' : 'alert'}
              />
              <StatCard label="Flagged transactions" value={summary.flagged_transactions} accent="alert" />
            </div>

            {forecast && (
              <div className="mb-8 border border-line bg-white rounded px-5 py-4">
                <div className="text-xs uppercase tracking-wide text-ink/50 mb-1">
                  Predicted spend — {forecast.month}
                </div>
                <div className="font-nums text-2xl text-coral">{forecast.predicted_spend.toFixed(2)}</div>
                <p className="text-xs text-ink/50 mt-1">Based on your last 3 months of activity.</p>
              </div>
            )}

            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <section>
                <h3 className="text-sm uppercase tracking-wide text-ink/50 mb-3">Spend by category</h3>
                <CategoryBars data={summary.by_category} />
              </section>

              <section>
                <h3 className="text-sm uppercase tracking-wide text-ink/50 mb-3">Fraud alerts</h3>
                <FraudAlerts alerts={alerts} />
              </section>
            </div>

            <section className="mb-8">
              <AIInsights />
            </section>

            <div className="grid md:grid-cols-2 gap-8">
              <section>
                <h3 className="text-sm uppercase tracking-wide text-ink/50 mb-3">Add a transaction</h3>
                <AddTransactionForm onAdded={loadAll} />
              </section>

              <section>
                <ScanReceipt onAdded={loadAll} />
              </section>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
