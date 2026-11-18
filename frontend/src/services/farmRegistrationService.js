import apiClient from '../apiClient'

export default {
  mine: () => apiClient.getAllPages('/farm-registrations/mine'),
  pending: () => apiClient.getAllPages('/farm-registrations'),
  submit: (payload) => apiClient.post('/farm-registrations', payload),
  approve: (id) => apiClient.post(`/farm-registrations/${id}/approve`),
  reject: (id, review_note) => apiClient.post(`/farm-registrations/${id}/reject`, { review_note }),
}
