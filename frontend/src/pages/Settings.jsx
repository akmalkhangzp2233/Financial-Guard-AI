import { useEffect, useState } from 'react'
import api from '../api'
import Sidebar from '../components/Sidebar.jsx'

export default function Settings() {
  const [user, setUser] = useState(null)

  useEffect(() => {
    api.get('/auth/me').then((res) => setUser(res.data))
  }, [])

  return (
    <div className="flex min-h-screen bg-ivory">
      <Sidebar />
      <main className="flex-1 px-8 py-8 max-w-lg">
        <header className="mb-8">
          <h2 className="font-display text-3xl text-ink">Settings</h2>
        </header>

        {user && (
          <div className="border border-line bg-white rounded px-5 py-4 space-y-3">
            <div>
              <div className="text-xs uppercase tracking-wide text-ink/50">Full name</div>
              <div className="text-ink">{user.full_name}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-ink/50">Email</div>
              <div className="text-ink">{user.email}</div>
            </div>
          </div>
        )}

        <p className="text-xs text-ink/40 mt-6">
          Password changes and category management aren't wired up yet — the backend already has
          the pieces (Users, Categories tables); add a PATCH /auth/me endpoint when you're ready.
        </p>
      </main>
    </div>
  )
}
