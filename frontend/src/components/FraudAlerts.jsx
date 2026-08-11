export default function FraudAlerts({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return <p className="text-sm text-ink/50">No flagged transactions. Your ledger looks clean.</p>
  }

  return (
    <div className="space-y-2">
      {alerts.map((a) => (
        <div key={a.id} className="flex items-start gap-3 border-l-4 border-alert bg-alert/5 rounded-r px-3 py-2">
          <div className="flex-1">
            <div className="text-sm text-ink">{a.reason}</div>
            <div className="text-xs text-ink/50 font-nums">
              Transaction #{a.transaction_id} · score {a.score.toFixed(2)}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
