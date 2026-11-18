import { useEffect, useState } from 'react'
import {
  administrativeLabel,
  communeFocus,
  getCommunes,
  getProvinces,
  provinceFocus,
} from '../services/administrativeGeographyService'

function uniqueNames(items) {
  return [...new Set(items.filter(Boolean))].sort((a, b) => a.localeCompare(b, 'vi'))
}

export default function AddressFields({ value, onChange, knownAddresses = [], idPrefix = 'address', onLocationFocus }) {
  const [provinces, setProvinces] = useState([])
  const [communes, setCommunes] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingCommunes, setLoadingCommunes] = useState(false)
  const [error, setError] = useState('')
  const [provinceCode, setProvinceCode] = useState('')
  const [communeCode, setCommuneCode] = useState('')
  const [customHamlet, setCustomHamlet] = useState(false)

  useEffect(() => {
    let active = true
    getProvinces()
      .then((data) => { if (active) setProvinces(data) })
      .catch(() => { if (active) setError('Không thể tải danh mục tỉnh/xã. Bạn vẫn có thể nhập địa chỉ thủ công bên dưới.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (value.province) return
    setProvinceCode('')
    setCommuneCode('')
    setCommunes([])
    setCustomHamlet(false)
  }, [value.province])

  const chooseProvince = async (event) => {
    const item = provinces.find((province) => String(province.code) === event.target.value)
    setProvinceCode(item ? String(item.code) : '')
    setCommuneCode('')
    setCommunes([])
    setCustomHamlet(false)
    onChange({ province: item ? administrativeLabel(item) : '', district: '', commune: '', hamlet: '' })
    onLocationFocus?.(provinceFocus(item))
    if (!item) return

    setLoadingCommunes(true)
    setError('')
    try {
      setCommunes(await getCommunes(item.code))
    } catch {
      setError('Không tải được danh sách xã/phường. Vui lòng thử lại hoặc nhập địa chỉ thủ công.')
    } finally {
      setLoadingCommunes(false)
    }
  }

  const chooseCommune = (event) => {
    const item = communes.find((commune) => String(commune.code) === event.target.value)
    setCommuneCode(item ? String(item.code) : '')
    setCustomHamlet(false)
    onChange({ district: '', commune: item ? administrativeLabel(item) : '', hamlet: '' })
    onLocationFocus?.(item
      ? communeFocus(item)
      : provinceFocus(provinces.find((province) => String(province.code) === provinceCode)))
  }

  const hamlets = uniqueNames(knownAddresses
    .filter((address) => address.province === value.province && address.commune === value.commune)
    .map((address) => address.hamlet))

  if (error) {
    return (
      <div>
        <p className="address-error" role="status">{error}</p>
        <div className="grid two address-fields">
          <div className="field"><label htmlFor={`${idPrefix}-province-manual`}>Tỉnh / thành phố</label><input id={`${idPrefix}-province-manual`} maxLength="100" value={value.province || ''} onChange={(e) => onChange({ province: e.target.value, district: '', commune: '', hamlet: '' })} required /></div>
          <div className="field"><label htmlFor={`${idPrefix}-commune-manual`}>Xã / phường / đặc khu</label><input id={`${idPrefix}-commune-manual`} maxLength="100" value={value.commune || ''} onChange={(e) => onChange({ district: '', commune: e.target.value, hamlet: '' })} required /></div>
          <div className="field"><label htmlFor={`${idPrefix}-hamlet-manual`}>Thôn / ấp / tổ dân phố</label><input id={`${idPrefix}-hamlet-manual`} maxLength="150" value={value.hamlet || ''} onChange={(e) => onChange({ hamlet: e.target.value })} required /></div>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="grid two address-fields">
        <div className="field">
          <label htmlFor={`${idPrefix}-province`}>Tỉnh / thành phố</label>
          <select id={`${idPrefix}-province`} value={provinceCode} onChange={chooseProvince} disabled={loading} required>
            <option value="">{loading ? 'Đang tải tỉnh/thành…' : 'Chọn tỉnh/thành'}</option>
            {provinces.map((item) => <option key={item.code} value={item.code}>{administrativeLabel(item)}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor={`${idPrefix}-commune`}>Xã / phường / đặc khu</label>
          <select id={`${idPrefix}-commune`} value={communeCode} onChange={chooseCommune} disabled={!provinceCode || loadingCommunes} required>
            <option value="">{loadingCommunes ? 'Đang tải xã/phường…' : 'Chọn xã/phường'}</option>
            {communes.map((item) => <option key={item.code} value={item.code}>{administrativeLabel(item)}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor={`${idPrefix}-hamlet`}>Thôn / ấp / tổ dân phố</label>
          <select
            id={`${idPrefix}-hamlet`}
            value={customHamlet ? '__custom__' : (hamlets.includes(value.hamlet) ? value.hamlet : '')}
            onChange={(event) => {
              if (event.target.value === '__custom__') {
                setCustomHamlet(true)
                onChange({ hamlet: '' })
              } else {
                setCustomHamlet(false)
                onChange({ hamlet: event.target.value })
              }
            }}
            disabled={!value.commune}
            required
          >
            <option value="">{value.commune ? (hamlets.length ? 'Chọn thôn/tổ dân phố' : 'Chưa có thôn trong danh sách') : 'Chọn xã/phường trước'}</option>
            {hamlets.map((name) => <option key={name} value={name}>{name}</option>)}
            <option value="__custom__">Nhập thôn/tổ dân phố khác…</option>
          </select>
          {customHamlet && <input className="hamlet-custom" aria-label="Tên thôn hoặc tổ dân phố" maxLength="150" value={value.hamlet || ''} onChange={(event) => onChange({ hamlet: event.target.value })} placeholder="Nhập tên thôn, ấp hoặc tổ dân phố" required />}
          <small className="address-hint">Danh sách gợi ý lấy từ các trang trại đã đăng ký trong xã; chọn “Nhập thôn khác” nếu chưa có.</small>
        </div>
      </div>
      <p className="address-hint">Địa chỉ hành chính mới gồm tỉnh/thành và xã/phường; huyện cũ được để trống với hồ sơ mới.</p>
      <p className="address-hint">Tọa độ địa giới hành chính: <a href="https://tinhthanhpho.com/en/api-docs" target="_blank" rel="noreferrer">tinhthanhpho.com</a> (CC BY 4.0).</p>
    </>
  )
}
