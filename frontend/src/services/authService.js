import api from './api'

export const login = (email, password) => api.post('/api/auth/login', { email, password })

export const logout = () => {
  localStorage.clear()
  window.location.href = '/login'
}

export const getUser = () => JSON.parse(localStorage.getItem('user') || 'null')

export const getToken = () => localStorage.getItem('token')
