const API = 'https://tinhthanhpho.com/api/v1'
const PAGE_SIZE = 100

async function getPage(path, page) {
  const separator = path.includes('?') ? '&' : '?'
  const response = await fetch(`${API}${path}${separator}limit=${PAGE_SIZE}&page=${page}`, {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) throw new Error('Không tải được danh mục địa chỉ hiện hành.')
  const payload = await response.json()
  if (!payload.success || !Array.isArray(payload.data)) {
    throw new Error('Dữ liệu địa giới hành chính không hợp lệ.')
  }
  return payload
}

async function getAll(path) {
  const records = []
  let page = 1
  let total = Infinity
  while (records.length < total) {
    const result = await getPage(path, page)
    records.push(...result.data)
    total = Number(result.metadata?.total) || records.length
    if (result.data.length < PAGE_SIZE) break
    page += 1
  }
  return records
}

export function getProvinces() {
  return getAll('/new-provinces')
}

export function getCommunes(provinceCode) {
  return getAll(`/new-provinces/${encodeURIComponent(provinceCode)}/wards`)
}

export function administrativeLabel(item) {
  return [item?.type, item?.name].filter(Boolean).join(' ')
}

function makeFocus(item, level, zoom) {
  const latitude = Number(item?.centroid_lat)
  const longitude = Number(item?.centroid_lng)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null
  return {
    key: `${level}-${item.code}`,
    center: [latitude, longitude],
    zoom,
  }
}

export function provinceFocus(province) {
  return makeFocus(province, 'province', 10.5)
}

export function communeFocus(commune) {
  return makeFocus(commune, 'commune', 15.5)
}
