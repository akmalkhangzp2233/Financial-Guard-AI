import { useEffect, useState } from 'react'
import { useNavigate, NavLink } from 'react-router-dom'
import api from '../api'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/budgets', label: 'Budgets' },
  { to: '/settings', label: 'Settings' },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    api.get('/auth/me').then((res) => setIsAdmin(!!res.data.is_admin)).catch(() => {})
  }, [])

  function logout() {
    localStorage.removeItem('finguard_token')
    navigate('/login')
  }

  return (
    <aside className="w-56 shrink-0 border-r border-line bg-white/60 min-h-screen px-5 py-8">
      <h1 className="font-display text-2xl text-ink mb-10">FinGuard AI</h1>
      <nav className="space-y-3 text-sm">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) =>
              `block ${isActive ? 'text-ink font-medium' : 'text-ink/60 hover:text-ink'}`
            }
          >
            {link.label}
          </NavLink>
        ))}
        {isAdmin && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `block ${isActive ? 'text-ink font-medium' : 'text-ink/60 hover:text-ink'}`
            }
          >
            Admin
          </NavLink>
        )}
      </nav>
      <button onClick={logout} className="mt-10 text-sm text-alert hover:underline">
        Sign out
      </button>
    </aside>
  )
}
