import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LogIn, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import api from '../api'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const res = await api.post('/auth/login', { email, password })
      localStorage.setItem('finguard_token', res.data.access_token)
      navigate('/')
    } catch (err) {
      setError('Wrong email or password. Try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-indigo/10 via-ivory to-coral/10">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-xl shadow-ink/5 border border-line px-8 py-10">
        <h1 className="font-display text-3xl text-ink mb-1 text-center">Welcome back</h1>
        <p className="text-ink/60 text-sm mb-8 text-center">Your ledger has been waiting for you.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs uppercase tracking-wide text-ink/50">Email</label>
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="mt-1 w-full border border-line bg-white px-3 py-2.5 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo placeholder:text-ink/30"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-ink/50">Password</label>
            <div className="relative mt-1">
              <input
                type={showPassword ? 'text' : 'password'} required value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full border border-line bg-white px-3 py-2.5 pr-10 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo placeholder:text-ink/30"
              />
              <button
                type="button" onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/40 hover:text-ink/70"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          {error && <p className="text-alert text-sm">{error}</p>}
          <button
            type="submit" disabled={submitting}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo to-indigo-light text-white py-2.5 rounded-lg font-medium hover:opacity-90 transition disabled:opacity-60"
          >
            <LogIn size={18} />
            {submitting ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <p className="text-sm text-ink/60 mt-6 text-center">
          Don't have an account? <Link to="/register" className="text-indigo font-semibold">Create one</Link>
        </p>

        <div className="border-t border-line mt-6 pt-4 flex items-center justify-center gap-1.5 text-xs text-ink/40">
          <ShieldCheck size={14} />
          Bank-level encryption &middot; Your data stays private
        </div>
      </div>
    </div>
  )
}
