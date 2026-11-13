import apiClient from '../apiClient'

export default {
  all: () => apiClient.get('/alerts'),
  get: (id) => apiClient.get(`/alerts/${id}`),
  create: (payload) => apiClient.post('/alerts', payload),
  update: (id, payload) => apiClient.put(`/alerts/${id}`, payload),
  remove: (id) => apiClient.delete(`/alerts/${id}`),
}
