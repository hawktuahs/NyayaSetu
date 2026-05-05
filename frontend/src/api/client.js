import axios from 'axios'

const api = axios.create({
  baseURL: '',  // use Vite proxy — /api/* → localhost:8000
  timeout: 30000,
})

export const healthCheck      = () => api.get('/api/health')
export const listCases        = () => api.get('/api/cases')
export const getCase          = (id) => api.get(`/api/cases/${id}`)
export const uploadCase       = (form) => api.post('/api/cases/upload', form)
export const retryExtraction  = (id) => api.post(`/api/cases/${id}/retry`)
export const getPdf = (id) => `/api/cases/${id}/pdf`

export const getVerification  = (id) => api.get(`/api/verify/${id}`)
export const submitVerification = (id, payload) => api.post(`/api/verify/${id}`, payload)
export const getVerificationHistory = (id) => api.get(`/api/verify/${id}/history`)

export const getDashboardCases = (params) => api.get('/api/dashboard', { params })
export const getDashboardStats = () => api.get('/api/dashboard/stats')

export const chatWithDocument = (id, messages) => api.post(`/api/cases/${id}/chat`, { messages })
