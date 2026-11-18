import apiClient from '../apiClient'

export default {
  all: () => apiClient.get('/auth/users'),
  create: (payload) => apiClient.post('/auth/users', payload),
  update: (id, payload) => apiClient.put(`/auth/users/${id}`, payload),
  remove: (id) => apiClient.delete(`/auth/users/${id}`),
}
