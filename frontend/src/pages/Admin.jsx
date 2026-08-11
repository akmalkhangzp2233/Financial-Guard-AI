import { useEffect, useState, useCallback } from 'react'
import { Navigate } from 'react-router-dom'
import api from '../api'
import Sidebar from '../components/Sidebar.jsx'
import StatCard from '../components/StatCard.jsx'

export default function Admin() {
  const [me, setMe] = useState(null)
  const [meLoaded, setMeLoaded] = useState(false)
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [fraudLogs, setFraudLogs] = useState([])
  const [tab, setTab] = useState('overview')
  const [loading, setLoading] = useState(true)

  const loadAll = useCallback(async () => {
    setLoading(true)
    const [statsRes, usersRes, logsRes] = await Promise.all([
      api.get('/admin/stats'),
      api.get('/admin/users'),
      api.get('/admin/fraud-logs'),
    ])
    setStats(statsRes.data)
    setUsers(usersRes.data)
    setFraudLogs(logsRes.data)
    setLoading(false)
  }, [])

  useEffect(() => {
    api.get('/auth/me').then((res) => {
      setMe(res.data)
      setMeLoaded(true)
    })
  }, [])

  useEffect(() => {
    if (me?.is_admin) loadAll()
  }, [me, loadAll])

  async function toggleActive(userId) {
    await api.patch(`/admin/users/${userId}/toggle-active`)
    loadAll()
  }

  async function toggleAdmin(userId) {
    await api.patch(`/admin/users/${userId}/toggle-admin`)
    loadAll()
  }

  async function markReviewed(logId) {
    await api.patch(`/admin/fraud-logs/${logId}/review`)
    loadAll()
  }

  // Wait for the /auth/me check before deciding whether to redirect — otherwise
  // a hard refresh on /admin briefly flashes a redirect for a legitimate admin.
  if (meLoaded && !me?.is_admin) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="flex min-h-screen bg-ivory">
      <Sidebar />
      <main className="flex-1 px-8 py-8 max-w-6xl">
        <header className="mb-8">
          <div className="text-xs uppercase tracking-wide text-ink/50">Admin</div>
          <h2 className="font-display text-3xl text-ink">Platform overview</h2>
        </header>

        {loading && <p className="text-ink/50">Loading…</p>}

        {!loading && stats && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard label="Total users" value={stats.total_users} />
              <StatCard label="Active users" value={stats.active_users} accent="indigo" />
              <StatCard label="Total transactions" value={stats.total_transactions} />
              <StatCard label="Flagged transactions" value={stats.total_flagged} accent="alert" />
              <StatCard label="Total volume" value={stats.total_volume.toFixed(2)} accent="coral" />
              <StatCard label="Receipt scans" value={stats.total_receipt_scans} />
              <StatCard label="Signups (7d)" value={stats.signups_last_7_days} accent="indigo" />
            </div>

            <div className="flex gap-6 border-b border-line mb-6 text-sm">
              {['overview', 'users', 'fraud'].map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`pb-3 -mb-px border-b-2 capitalize ${
                    tab === t ? 'border-ink text-ink font-medium' : 'border-transparent text-ink/50 hover:text-ink'
                  }`}
                >
                  {t === 'fraud' ? 'Fraud review' : t}
                </button>
              ))}
            </div>

            {tab === 'overview' && (
              <div className="border border-line bg-white rounded px-5 py-4">
                <p className="text-sm text-ink/70">
                  {stats.total_flagged} of {stats.total_transactions} transactions across the platform have been
                  flagged by the fraud model ({stats.total_transactions ? ((stats.total_flagged / stats.total_transactions) * 100).toFixed(1) : '0'}%).
                  Switch to the <button onClick={() => setTab('fraud')} className="text-indigo hover:underline">Fraud review</button> tab
                  to work through unreviewed alerts, or <button onClick={() => setTab('users')} className="text-indigo hover:underline">Users</button> to
                  manage accounts.
                </p>
                <a
                  href={`${api.defaults.baseURL}/reports/export/all-transactions.csv`}
                  className="inline-block mt-4 text-sm text-indigo hover:underline"
                  onClick={(e) => {
                    // CSV download needs the auth header, which a plain <a> can't attach —
                    // fetch it via axios instead and trigger a blob download.
                    e.preventDefault()
                    api.get('/reports/export/all-transactions.csv', { responseType: 'blob' }).then((res) => {
                      const url = URL.createObjectURL(new Blob([res.data]))
                      const link = document.createElement('a')
                      link.href = url
                      link.download = 'finguard_all_transactions.csv'
                      link.click()
                      URL.revokeObjectURL(url)
                    })
                  }}
                >
                  ↓ Export all transactions as CSV (for Power BI / Excel)
                </a>
              </div>
            )}

            {tab === 'users' && (
              <div className="border border-line bg-white rounded overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-ink/50 border-b border-line">
                      <th className="px-4 py-3">Name</th>
                      <th className="px-4 py-3">Email</th>
                      <th className="px-4 py-3">Transactions</th>
                      <th className="px-4 py-3">Total spent</th>
                      <th className="px-4 py-3">Flagged</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Role</th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id} className="border-b border-line last:border-0">
                        <td className="px-4 py-3 text-ink">{u.full_name}</td>
                        <td className="px-4 py-3 text-ink/70">{u.email}</td>
                        <td className="px-4 py-3 font-nums">{u.transaction_count}</td>
                        <td className="px-4 py-3 font-nums">{u.total_spent.toFixed(2)}</td>
                        <td className="px-4 py-3 font-nums">{u.flagged_count}</td>
                        <td className="px-4 py-3">
                          <span className={u.is_active ? 'text-indigo' : 'text-alert'}>
                            {u.is_active ? 'Active' : 'Disabled'}
                          </span>
                        </td>
                        <td className="px-4 py-3">{u.is_admin ? 'Admin' : 'User'}</td>
                        <td className="px-4 py-3 text-right space-x-3 whitespace-nowrap">
                          <button onClick={() => toggleActive(u.id)} className="text-xs text-ink/60 hover:text-ink hover:underline">
                            {u.is_active ? 'Disable' : 'Enable'}
                          </button>
                          <button onClick={() => toggleAdmin(u.id)} className="text-xs text-ink/60 hover:text-ink hover:underline">
                            {u.is_admin ? 'Revoke admin' : 'Make admin'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {tab === 'fraud' && (
              <div className="border border-line bg-white rounded overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-ink/50 border-b border-line">
                      <th className="px-4 py-3">Transaction</th>
                      <th className="px-4 py-3">User</th>
                      <th className="px-4 py-3">Score</th>
                      <th className="px-4 py-3">Reason</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {fraudLogs.length === 0 && (
                      <tr><td colSpan={6} className="px-4 py-6 text-center text-ink/50">No fraud alerts yet.</td></tr>
                    )}
                    {fraudLogs.map((l) => (
                      <tr key={l.id} className="border-b border-line last:border-0">
                        <td className="px-4 py-3 font-nums">#{l.transaction_id}</td>
                        <td className="px-4 py-3 text-ink/70">{l.user_email}</td>
                        <td className="px-4 py-3 font-nums">{l.score.toFixed(2)}</td>
                        <td className="px-4 py-3 text-ink/70">{l.reason}</td>
                        <td className="px-4 py-3">
                          <span className={l.reviewed ? 'text-indigo' : 'text-alert'}>
                            {l.reviewed ? 'Reviewed' : 'Pending'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          {!l.reviewed && (
                            <button onClick={() => markReviewed(l.id)} className="text-xs text-indigo hover:underline">
                              Mark reviewed
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
