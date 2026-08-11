import axios from 'axios'

// In production this comes from the VITE_API_URL build-time env var (set it in
// Vercel/Netlify project settings, or in the frontend/.env file for local prod
// builds). Falls back to the local FastAPI dev server so `npm run dev` still
// works with zero config.
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL })

// Attach the JWT (if we have one) to every request automatically.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('finguard_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Centralized 401 handling: an expired/invalid token should always drop the
// user back to /login instead of leaving the app stuck on a broken screen.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      localStorage.removeItem('finguard_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
