import axios from 'axios'

// --------------------------------------------------
// API configuration
// --------------------------------------------------

const baseURL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// --------------------------------------------------
// Authentication
// Attach the saved JWT to every request.
// --------------------------------------------------

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('finguard_token')

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

// --------------------------------------------------
// API methods
// --------------------------------------------------

/**
 * Retrieve the latest fraud alerts for the logged-in user.
 */
export const fetchFraudAlerts = () => {
  return api.get('/insights/fraud-alerts')
}

/**
 * Mark a fraud alert as reviewed.
 * The backend verifies that the alert belongs to the logged-in user.
 *
 * @param {number} alertId - The fraud alert's database ID.
 */
export const markFraudAlertReviewed = (alertId) => {
  if (!Number.isInteger(Number(alertId)) || Number(alertId) <= 0) {
    return Promise.reject(new Error('A valid fraud alert ID is required.'))
  }

  return api.patch(
    `/insights/fraud-alerts/${Number(alertId)}/review`
  )
}

/**
 * Retrieve the dashboard summary.
 */
export const fetchDashboardSummary = () => {
  return api.get('/insights/summary')
}

/**
 * Retrieve the spending forecast.
 */
export const fetchForecast = () => {
  return api.get('/insights/forecast')
}

// --------------------------------------------------
// Error helper
// --------------------------------------------------

/**
 * Return a readable message for an API error.
 */
export const getApiErrorMessage = (
  error,
  fallback = 'Something went wrong. Please try again.'
) => {
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail

    return typeof detail === 'string'
      ? detail
      : fallback
  }

  if (error.code === 'ECONNABORTED') {
    return 'The request timed out. Please try again.'
  }

  if (!error.response && error.request) {
    return 'Cannot connect to the server. Check that the backend is running.'
  }

  return error.message || fallback
}

// --------------------------------------------------
// Default export
// Preserve compatibility with existing imports:
// import api from '../api'
// --------------------------------------------------

export default api
