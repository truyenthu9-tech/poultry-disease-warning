import apiClient from '../apiClient'

export default {
  all: () => apiClient.getAllPages('/alerts'),
  forOutbreak: (outbreakId) => apiClient.getAllPages(`/alerts?outbreak_id=${encodeURIComponent(outbreakId)}`),
  get: (id) => apiClient.get(`/alerts/${id}`),
  create: (payload) => apiClient.post('/alerts', payload),
  update: (id, payload) => apiClient.put(`/alerts/${id}`, payload),
  remove: (id) => apiClient.delete(`/alerts/${id}`),
  acknowledge: (id) => apiClient.patch(`/alerts/${id}/acknowledge`),
  generateForOutbreak: (outbreakId) => apiClient.post(`/alerts/outbreaks/${outbreakId}/generate`),
}
