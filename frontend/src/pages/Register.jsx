import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UserPlus, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import api from '../api'

export default function Register() {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  const initial = fullName.trim().charAt(0).toUpperCase() || 'F'

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    setSubmitting(true)
    try {
      await api.post('/auth/register', { full_name: fullName, email, password })
      const res = await api.post('/auth/login', { email, password })
      localStorage.setItem('finguard_token', res.data.access_token)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create account.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-indigo/10 via-ivory to-coral/10">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-xl shadow-ink/5 border border-line px-8 py-10">
        <div className="flex justify-center mb-5">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo to-coral flex items-center justify-center text-white text-2xl font-bold shadow-md">
            {initial}
          </div>
        </div>
        <h1 className="font-display text-3xl text-ink mb-1 text-center">Join FinGuard AI</h1>
        <p className="text-ink/60 text-sm mb-8 text-center">Take control of your finances, starting now.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs uppercase tracking-wide text-ink/50">Your Name</label>
            <input required value={fullName} onChange={(e) => setFullName(e.target.value)}
              placeholder="What should we call you?"
              className="mt-1 w-full border border-line bg-white px-3 py-2.5 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo placeholder:text-ink/30" />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-ink/50">Email</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="mt-1 w-full border border-line bg-white px-3 py-2.5 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo placeholder:text-ink/30" />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-ink/50">Password</label>
            <div className="relative mt-1">
              <input
                type={showPassword ? 'text' : 'password'} required value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
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
          <div>
            <label className="text-xs uppercase tracking-wide text-ink/50">Confirm Password</label>
            <div className="relative mt-1">
              <input
                type={showConfirm ? 'text' : 'password'} required value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
                className="w-full border border-line bg-white px-3 py-2.5 pr-10 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo placeholder:text-ink/30"
              />
              <button
                type="button" onClick={() => setShowConfirm((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/40 hover:text-ink/70"
                tabIndex={-1}
              >
                {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          {error && <p className="text-alert text-sm">{error}</p>}
          <button
            type="submit" disabled={submitting}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo to-coral text-white py-2.5 rounded-lg font-medium hover:opacity-90 transition disabled:opacity-60"
          >
            <UserPlus size={18} />
            {submitting ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p className="text-sm text-ink/60 mt-6 text-center">
          Already have one? <Link to="/login" className="text-indigo font-semibold">Sign in</Link>
        </p>

        <div className="border-t border-line mt-6 pt-4 flex items-center justify-center gap-1.5 text-xs text-ink/40">
          <ShieldCheck size={14} />
          Bank-level encryption &middot; Your data stays private
        </div>
      </div>
    </div>
  )
}
