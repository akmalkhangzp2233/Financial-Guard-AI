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
  const [dashboardError, setDashboardError] = useState('')

  // --------------------------------------------------
  // Load dashboard data
  // --------------------------------------------------

  const loadAll = useCallback(async () => {
    setLoading(true)
    setDashboardError('')

    try {
      const [summaryResponse, alertsResponse, forecastResponse] =
        await Promise.all([
          api.get('/insights/summary'),
          api.get('/insights/fraud-alerts'),
          api.get('/insights/forecast'),
        ])

      setSummary(summaryResponse.data)
      setAlerts(alertsResponse.data)
      setForecast(forecastResponse.data)
    } catch (error) {
      console.error('Failed to load dashboard:', error)

      setDashboardError(
        error.response?.data?.detail ||
          'Unable to load dashboard data. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  // --------------------------------------------------
  // Update a fraud alert after successful review
  // --------------------------------------------------

  const handleAlertReviewed = useCallback((updatedAlert) => {
    setAlerts((previousAlerts) =>
      previousAlerts.map((alert) =>
        alert.id === updatedAlert.id
          ? {
              ...alert,
              ...updatedAlert,
              reviewed: true,
            }
          : alert
      )
    )
  }, [])

  // --------------------------------------------------
  // Loading state
  // --------------------------------------------------

  if (loading) {
    return (
      <div className="flex min-h-screen bg-ivory">
        <Sidebar />

        <main className="flex-1 px-8 py-8 max-w-5xl">
          <p className="text-ink/50" role="status">
            Loading your dashboard...
          </p>
        </main>
      </div>
    )
  }

  // --------------------------------------------------
  // Dashboard error state
  // --------------------------------------------------

  if (dashboardError && !summary) {
    return (
      <div className="flex min-h-screen bg-ivory">
        <Sidebar />

        <main className="flex-1 px-8 py-8 max-w-5xl">
          <h2 className="font-display text-3xl text-ink mb-4">
            Dashboard unavailable
          </h2>

          <p className="text-sm text-red-500 mb-4" role="alert">
            {dashboardError}
          </p>

          <button
            type="button"
            onClick={loadAll}
            className="rounded-md border border-line bg-white px-4 py-2 text-sm text-ink hover:bg-ink/5"
          >
            Try again
          </button>
        </main>
      </div>
    )
  }

  // --------------------------------------------------
  // Main dashboard
  // --------------------------------------------------

  return (
    <div className="flex min-h-screen bg-ivory">
      <Sidebar />

      <main className="flex-1 px-8 py-8 max-w-5xl">
        <header className="mb-8">
          <div className="text-xs uppercase tracking-wide text-ink/50">
            Overview
          </div>

          <h2 className="font-display text-3xl text-ink">
            This month's ledger
          </h2>
        </header>

        {dashboardError && (
          <div
            role="alert"
            className="mb-6 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3"
          >
            <p className="text-sm text-red-500">
              {dashboardError}
            </p>

            <button
              type="button"
              onClick={loadAll}
              className="mt-2 text-sm font-medium text-ink underline"
            >
              Reload dashboard
            </button>
          </div>
        )}

        {/* Summary cards */}

        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Total spent"
              value={Number(summary.total_spent ?? 0).toFixed(2)}
            />

            <StatCard
              label="Total income"
              value={Number(summary.total_income ?? 0).toFixed(2)}
              accent="indigo"
            />

            <StatCard
              label="Net savings"
              value={Number(summary.savings ?? 0).toFixed(2)}
              accent={
                Number(summary.savings ?? 0) >= 0
                  ? 'indigo'
                  : 'alert'
              }
            />

            <StatCard
              label="Flagged transactions"
              value={Number(summary.flagged_transactions ?? 0)}
              accent="alert"
            />
          </div>
        )}

        {/* Spending forecast */}

        {forecast && (
          <section className="mb-8 border border-line bg-white rounded px-5 py-4">
            <div className="text-xs uppercase tracking-wide text-ink/50 mb-1">
              Predicted spend — {forecast.month}
            </div>

            <div className="font-nums text-2xl text-coral">
              {Number(forecast.predicted_spend ?? 0).toFixed(2)}
            </div>

            <p className="text-xs text-ink/50 mt-1">
              Forecast based on available transaction history.
              Predictions are estimates, not guaranteed outcomes.
            </p>
          </section>
        )}

        {/* Category breakdown and fraud alerts */}

        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <section>
            <h3 className="text-sm uppercase tracking-wide text-ink/50 mb-3">
              Spend by category
            </h3>

            <CategoryBars data={summary?.by_category ?? []} />
          </section>

          <section>
            <h3 className="text-sm uppercase tracking-wide text-ink/50 mb-3">
              Fraud alerts
            </h3>

            <FraudAlerts
              alerts={alerts}
              onReviewed={handleAlertReviewed}
            />
          </section>
        </div>

        {/* AI insights */}

        <section className="mb-8">
          <AIInsights />
        </section>

        {/* Transaction and receipt tools */}

        <div className="grid md:grid-cols-2 gap-8">
          <section>
            <h3 className="text-sm uppercase tracking-wide text-ink/50 mb-3">
              Add a transaction
            </h3>

            <AddTransactionForm onAdded={loadAll} />
          </section>

          <section>
            <ScanReceipt onAdded={loadAll} />
          </section>
        </div>
      </main>
    </div>
  )
}