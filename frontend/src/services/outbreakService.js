import apiClient from '../apiClient'

export default {
  all: () => apiClient.getAllPages('/outbreaks'),
  get: (id) => apiClient.get(`/outbreaks/${id}`),
  create: (payload) => apiClient.post('/outbreaks', payload),
  update: (id, payload) => apiClient.put(`/outbreaks/${id}`, payload),
  remove: (id) => apiClient.delete(`/outbreaks/${id}`),
  verify: (id) => apiClient.post(`/outbreaks/${id}/verify`),
  importFromSources: () => apiClient.post('/outbreaks/import'),
  nearbyFarms: (id, radiusKm) => apiClient.get(`/outbreaks/${id}/nearby-farms${radiusKm ? `?radius_km=${radiusKm}` : ''}`),
}
