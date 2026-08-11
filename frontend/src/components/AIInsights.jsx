import { useState } from 'react'
import api from '../api'

export default function AIInsights({ initial = [] }) {
  const [tips, setTips] = useState(initial)
  const [loading, setLoading] = useState(false)

  async function refresh() {
    setLoading(true)
    try {
      const res = await api.post('/insights/ai-advice')
      setTips(res.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="border border-line bg-white rounded px-5 py-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm uppercase tracking-wide text-ink/50">AI savings tips</h3>
        <button onClick={refresh} disabled={loading} className="text-xs text-indigo hover:underline disabled:opacity-50">
          {loading ? 'Thinking…' : 'Refresh'}
        </button>
      </div>
      {tips.length === 0 ? (
        <p className="text-sm text-ink/50">Tap refresh to get personalized tips from your spending.</p>
      ) : (
        <ul className="space-y-2">
          {tips.map((t) => (
            <li key={t.id} className="text-sm text-ink/80">
              {t.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
