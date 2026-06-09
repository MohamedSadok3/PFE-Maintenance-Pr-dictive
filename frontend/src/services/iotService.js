import api from './api'

export const getIoTConfig = () => api.get('/api/iot/config')

export const saveIoTConfig = (payload) => api.post('/api/iot/config', payload)

export const testMqttConnection = (payload) => api.post('/api/iot/config/test', payload)
