import api from './api'
import { getStoredUser } from '../utils/storage'

export const login = (email, password) => api.post('/api/auth/login', { email, password })
export const registerPlant = (payload) => api.post('/api/auth/register-plant', payload)
export const getRegistrations = (params) => api.get('/api/auth/registrations', { params })
export const reviewRegistration = (id, payload) => api.patch(`/api/auth/registrations/${id}/review`, payload)
export const getMyPlant = () => api.get('/api/plants/me')
export const updateMyPlant = (payload) => api.patch('/api/plants/me', payload)
export const getPlants = (params) => api.get('/api/plants', { params })
export const updatePlant = (id, payload) => api.patch(`/api/plants/${id}`, payload)

export const logout = () => {
  localStorage.clear()
  window.location.href = '/login'
}

export const getUser = () => getStoredUser()

export const getToken = () => localStorage.getItem('token')
