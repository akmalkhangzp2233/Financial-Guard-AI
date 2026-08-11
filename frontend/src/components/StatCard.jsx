export default function StatCard({ label, value, accent = 'ink' }) {
  const colorClass = {
    ink: 'text-ink',
    indigo: 'text-indigo',
    alert: 'text-alert',
    coral: 'text-coral',
  }[accent]

  return (
    <div className="border border-line bg-white rounded px-5 py-4">
      <div className="text-xs uppercase tracking-wide text-ink/50 mb-2">{label}</div>
      <div className={`font-nums text-2xl ${colorClass}`}>{value}</div>
    </div>
  )
}
