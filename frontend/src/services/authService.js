import apiClient from '../apiClient'

const authService = {
  login: async (payload) => {
    const result = await apiClient.post('/auth/login', payload)
    if (result?.access_token) localStorage.setItem('access_token', result.access_token)
    return result?.user ?? result
  },
  register: async (payload) => {
    const result = await apiClient.post('/auth/register', payload)
    if (result?.access_token) localStorage.setItem('access_token', result.access_token)
    return result?.user ?? result
  },
  current: () => apiClient.get('/auth/me'),
  logout: () => localStorage.removeItem('access_token'),
}
export default authService
