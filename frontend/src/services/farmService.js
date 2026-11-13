import apiClient from '../apiClient'

export default {
  all: () => apiClient.get('/farms'),
  get: (id) => apiClient.get(`/farms/${id}`),
  create: (payload) => apiClient.post('/farms', payload),
  update: (id, payload) => apiClient.put(`/farms/${id}`, payload),
  remove: (id) => apiClient.delete(`/farms/${id}`),
}
