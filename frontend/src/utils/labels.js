export const riskLabel = { low: 'Thấp', medium: 'Trung bình', high: 'Cao', critical: 'Nghiêm trọng' }
export const riskColor = { low: '#16a34a', medium: '#d97706', high: '#dc2626', critical: '#7f1d1d' }
export const alertStatusLabel = { pending: 'Chờ gửi', sent: 'Đã gửi', failed: 'Gửi lỗi', acknowledged: 'Đã xác nhận' }
export const outbreakStatusLabel = { active: 'Đang hoạt động', contained: 'Đã khống chế', closed: 'Đã đóng' }
export const poultryLabel = { chicken: 'Gà', duck: 'Vịt', muscovy: 'Ngan', quail: 'Chim cút', other: 'Khác' }

export const advisoryNotice =
  'Cảnh báo tham khảo, không phải kết luận hay chỉ đạo chính thức của cơ quan thú y. Hãy liên hệ cán bộ thú y địa phương để được hướng dẫn.'
export const sourceLabel = (source) => {
  if (!source || source === 'manual') return 'Cán bộ nhập'
  if (source === 'farm_registration') return 'Chủ trại báo cáo, đã xác nhận'
  if (source === 'user_report') return 'Người dùng báo cáo, đã xác nhận'
  return source.replace(/^feed:/, 'Nguồn ')
}

export const formatDate = (value) => (value ? new Date(value).toLocaleString('vi-VN') : '')
