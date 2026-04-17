import api from './api'

export const getAlertes = (params) => api.get('/api/alertes', { params })

export const assignAlert = (id, userId) =>
  api.patch(`/api/alertes/${id}`, {
    assigned_to: userId,
  })

export const resolveAlert = (id) =>
  api.patch(`/api/alertes/${id}`, {
    status: 'resolved',
  })

export const acknowledgeAlert = (id) =>
  api.patch(`/api/alertes/${id}`, {
    acknowledged: true,
  })
