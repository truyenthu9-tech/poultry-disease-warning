import apiClient from '../apiClient'

async function reportRequest(action) {
  try {
    return await action()
  } catch (error) {
    if (error.message === 'Not Found') {
      throw new Error('Backend chưa có API báo cáo dịch bệnh. Hãy khởi động lại backend từ thư mục backend, rồi chạy alembic upgrade head.')
    }
    throw error
  }
}

export default {
  mine: () => reportRequest(() => apiClient.getAllPages('/outbreak-reports/mine')),
  pending: () => reportRequest(() => apiClient.getAllPages('/outbreak-reports')),
  submit: (payload) => reportRequest(() => apiClient.post('/outbreak-reports', payload)),
  approve: (id) => reportRequest(() => apiClient.post(`/outbreak-reports/${id}/approve`)),
  reject: (id, review_note) => reportRequest(() => apiClient.post(`/outbreak-reports/${id}/reject`, { review_note })),
}
