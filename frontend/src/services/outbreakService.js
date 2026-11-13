import apiClient from '../apiClient'

export default {
  all: () => apiClient.get('/outbreaks'),
  get: (id) => apiClient.get(`/outbreaks/${id}`),
  create: (payload) => apiClient.post('/outbreaks', payload),
  update: (id, payload) => apiClient.put(`/outbreaks/${id}`, payload),
  remove: (id) => apiClient.delete(`/outbreaks/${id}`),
}
