import { useState } from "react"
import {
  markFraudAlertReviewed,
  getApiErrorMessage,
} from "../api"

const riskStyles = {
  High: {
    badge: "bg-red-500/10 text-red-500 border-red-500/20",
    border: "border-red-500",
  },
  Medium: {
    badge: "bg-orange-500/10 text-orange-500 border-orange-500/20",
    border: "border-orange-500",
  },
  Low: {
    badge: "bg-green-500/10 text-green-500 border-green-500/20",
    border: "border-green-500",
  },
}

const filters = ["All", "Pending", "Reviewed"]

export default function FraudAlerts({ alerts = [], onReviewed }) {
  const [updatingIds, setUpdatingIds] = useState([])
  const [error, setError] = useState("")
  const [activeFilter, setActiveFilter] = useState("All")

  const safeAlerts = Array.isArray(alerts) ? alerts : []

  const filteredAlerts = safeAlerts.filter((alert) => {
    if (activeFilter === "Pending") {
      return !alert.reviewed
    }

    if (activeFilter === "Reviewed") {
      return Boolean(alert.reviewed)
    }

    return true
  })

  const filterCounts = {
    All: safeAlerts.length,
    Pending: safeAlerts.filter((alert) => !alert.reviewed).length,
    Reviewed: safeAlerts.filter((alert) => Boolean(alert.reviewed)).length,
  }

  const handleMarkReviewed = async (alertId) => {
    if (updatingIds.includes(alertId)) return

    setError("")
    setUpdatingIds((previous) => [...previous, alertId])

    try {
      const response = await markFraudAlertReviewed(alertId)

      // Update the parent dashboard so the reviewed status persists
      // in the displayed list without requiring a page refresh.
      if (onReviewed) {
        onReviewed(
          response.data.alert ?? {
            id: alertId,
            reviewed: true,
          }
        )
      }
    } catch (err) {
      setError(
        getApiErrorMessage(
          err,
          "Unable to update this alert. Please try again."
        )
      )
    } finally {
      setUpdatingIds((previous) =>
        previous.filter((id) => id !== alertId)
      )
    }
  }

  return (
    <div className="space-y-3">
      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-500"
        >
          {error}
        </div>
      )}

      {/* Alert filters */}
      <div
        className="flex flex-wrap items-center gap-2"
        role="group"
        aria-label="Filter fraud alerts"
      >
        {filters.map((filter) => {
          const isActive = activeFilter === filter

          return (
            <button
              key={filter}
              type="button"
              onClick={() => setActiveFilter(filter)}
              aria-pressed={isActive}
              className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition ${
                isActive
                  ? "border-ink/30 bg-ink/10 text-ink"
                  : "border-ink/10 text-ink/60 hover:bg-ink/5 hover:text-ink"
              }`}
            >
              <span>{filter}</span>

              <span
                className={`rounded-full px-1.5 py-0.5 text-xs ${
                  isActive
                    ? "bg-ink/10 text-ink"
                    : "bg-ink/5 text-ink/50"
                }`}
              >
                {filterCounts[filter]}
              </span>
            </button>
          )
        })}
      </div>

      {/* Alert list */}
      {filteredAlerts.length === 0 ? (
        <p className="text-sm text-ink/50">
          {safeAlerts.length === 0
            ? "No flagged transactions. Your ledger looks clean."
            : activeFilter === "Pending"
              ? "No pending alerts. All alerts have been reviewed."
              : activeFilter === "Reviewed"
                ? "No reviewed alerts yet."
                : "No alerts found."}
        </p>
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((a) => {
            const riskLevel = riskStyles[a.risk_level]
              ? a.risk_level
              : "Medium"

            const styles = riskStyles[riskLevel]
            const isUpdating = updatingIds.includes(a.id)

            return (
              <div
                key={a.id}
                className={`flex items-start gap-3 border-l-4 ${styles.border} bg-alert/5 rounded-r px-3 py-3`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-ink">
                      Transaction #{a.transaction_id}
                    </span>

                    <span
                      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${styles.badge}`}
                    >
                      {riskLevel} Risk
                    </span>

                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs ${
                        a.reviewed
                          ? "bg-green-500/10 text-green-500"
                          : "bg-ink/5 text-ink/50"
                      }`}
                    >
                      {a.reviewed ? "Reviewed" : "Pending Review"}
                    </span>
                  </div>

                  <div className="text-sm text-ink">
                    {a.reason ||
                      "Unusual transaction pattern detected."}
                  </div>

                  <div className="text-xs text-ink/50 font-nums mt-1">
                    Anomaly score: {Number(a.score).toFixed(4)}
                  </div>

                  {a.created_at && (
                    <div className="text-xs text-ink/40 mt-1">
                      {new Date(a.created_at).toLocaleString()}
                    </div>
                  )}

                  {!a.reviewed && (
                    <button
                      type="button"
                      onClick={() => handleMarkReviewed(a.id)}
                      disabled={isUpdating}
                      className="mt-3 inline-flex items-center rounded-md border border-ink/15 px-3 py-1.5 text-xs font-medium text-ink transition hover:bg-ink/5 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {isUpdating
                        ? "Saving..."
                        : "Mark as Reviewed"}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}