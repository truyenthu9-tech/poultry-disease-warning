const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

// Backend (FastAPI) trả lỗi 422 dưới dạng mảng, đổi thành một câu dễ đọc
function extractMessage(data, status) {
  if (typeof data === 'string' && data) return data
  const detail = data?.detail ?? data?.message
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc.filter((p) => p !== 'body').join('.') : ''
        return field ? `${field}: ${d.msg}` : d.msg
      })
      .join('; ')
  }
  return `HTTP ${status}`
}

async function request(path, options = {}) {
  const token = localStorage.getItem('access_token')
  const headers = {
    Accept: 'application/json',
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  if (response.status === 204) return null
  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await response.json() : await response.text()
  if (!response.ok) {
    // Token hết hạn hoặc không hợp lệ: xóa token và báo cho App quay về đăng nhập
    if (response.status === 401 && token) {
      localStorage.removeItem('access_token')
      window.dispatchEvent(new Event('auth:unauthorized'))
    }
    throw new Error(extractMessage(data, response.status))
  }
  return data
}

const apiClient = {
  get: (path) => request(path),
  getAllPages: async (path) => {
    const records = []
    let page = 1
    let batch
    do {
      const separator = path.includes('?') ? '&' : '?'
      batch = await request(`${path}${separator}page=${page}&page_size=100`)
      if (!Array.isArray(batch)) return records
      records.push(...batch)
      page += 1
    } while (batch.length === 100)
    return records
  },
  post: (path, body) => request(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: 'PATCH', body: body === undefined ? undefined : JSON.stringify(body) }),
  delete: (path) => request(path, { method: 'DELETE' }),
}
export default apiClient
