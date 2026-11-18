import { useEffect, useState } from 'react'
import MapView from '../components/MapView'
import AddressFields from '../components/AddressFields'
import farmService from '../services/farmService'
import { poultryLabel } from '../utils/labels'

const emptyForm = {
  name: '', owner_name: '', phone: '', email: '', owner_user_email: '', province: '', district: '', commune: '', hamlet: '',
  poultry_type: 'chicken', capacity: 0, latitude: '', longitude: '',
}

export default function Farms({ canWrite = false }) {
  const [farms, setFarms] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [mapFocus, setMapFocus] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => farmService.all()
    .then(setFarms)
    .catch((err) => setError(err.message))
    .finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const pickedPoint = form.latitude !== '' && form.longitude !== ''
    ? { latitude: Number(form.latitude), longitude: Number(form.longitude) }
    : null
  const focusAddress = (focus) => {
    setMapFocus(focus)
    setForm((current) => ({ ...current, latitude: '', longitude: '' }))
  }

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await farmService.create({
        name: form.name,
        owner_name: form.owner_name,
        phone: form.phone,
        email: form.email.trim() || null,
        owner_user_email: form.owner_user_email.trim() || null,
        province: form.province,
        district: form.district || null,
        commune: form.commune || null,
        hamlet: form.hamlet.trim() || null,
        poultry_type: form.poultry_type,
        capacity: Number(form.capacity) || 0,
        location: { latitude: Number(form.latitude), longitude: Number(form.longitude) },
      })
      setForm(emptyForm)
      setShowForm(false)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const remove = async (farm) => {
    if (!window.confirm(`Xóa trang trại "${farm.name}"?`)) return
    try {
      await farmService.remove(farm.id)
      setFarms((list) => list.filter((f) => f.id !== farm.id))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page">
      <h1>Quản lý trang trại</h1>
      {canWrite
        ? <p><button className="btn" onClick={() => setShowForm(!showForm)}>{showForm ? 'Đóng form' : 'Thêm trang trại'}</button></p>
        : <p className="map-hint">Bạn chỉ có quyền xem. Thông tin liên hệ của chủ trại chỉ hiển thị với quản trị viên và cán bộ thú y.</p>}

      {canWrite && showForm && (
        <div className="card">
          <form onSubmit={handleSubmit}>
            <div className="grid two">
              <div className="field"><label htmlFor="farm-name">Tên trang trại</label><input id="farm-name" value={form.name} onChange={set('name')} required /></div>
              <div className="field"><label htmlFor="farm-owner">Chủ trại</label><input id="farm-owner" value={form.owner_name} onChange={set('owner_name')} required /></div>
              <div className="field"><label htmlFor="farm-phone">Số điện thoại</label><input id="farm-phone" value={form.phone} onChange={set('phone')} placeholder="0912345678" pattern="(0|\+84)\d{9}" title="Bắt đầu bằng 0 hoặc +84, theo sau là 9 chữ số" required /></div>
              <div className="field">
                <label htmlFor="farm-poultry">Loại gia cầm</label>
                <select id="farm-poultry" value={form.poultry_type} onChange={set('poultry_type')}>
                  {Object.entries(poultryLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </div>
              <AddressFields
                value={form}
                knownAddresses={farms.map(({ province, district, commune, hamlet }) => ({ province, district, commune, hamlet }))}
                idPrefix="farm"
                onLocationFocus={focusAddress}
                onChange={(address) => setForm((current) => ({ ...current, ...address }))}
              />
              <div className="field"><label htmlFor="farm-capacity">Quy mô (con)</label><input id="farm-capacity" type="number" min="0" value={form.capacity} onChange={set('capacity')} /></div>
              <div className="field"><label htmlFor="farm-notification-email">Email nhận cảnh báo</label><input id="farm-notification-email" type="email" value={form.email} onChange={set('email')} placeholder="chutrai@example.com" /></div>
              <div className="field">
                <label htmlFor="farm-account-email">Email tài khoản chủ trại (để xem cảnh báo)</label>
                <input id="farm-account-email" type="email" value={form.owner_user_email} onChange={set('owner_user_email')} placeholder="tài khoản đã đăng ký" />
              </div>
              <div />
              <div className="field"><label htmlFor="farm-latitude">Vĩ độ (latitude)</label><input id="farm-latitude" type="number" step="any" min="-90" max="90" value={form.latitude} onChange={set('latitude')} placeholder="21.137" required /></div>
              <div className="field"><label htmlFor="farm-longitude">Kinh độ (longitude)</label><input id="farm-longitude" type="number" step="any" min="-180" max="180" value={form.longitude} onChange={set('longitude')} placeholder="105.848" required /></div>
            </div>
            <p className="map-hint">Bấm lên bản đồ để chọn vị trí, vĩ độ và kinh độ sẽ tự điền.</p>
            <div className="picker">
              <MapView
                height={320}
                farms={farms}
                picked={pickedPoint}
                focus={mapFocus}
                onPick={(p) => setForm((f) => ({ ...f, latitude: String(p.latitude), longitude: String(p.longitude) }))}
              />
            </div>
            <button className="btn" type="submit" disabled={saving} style={{ marginTop: 12 }}>Lưu trang trại</button>
          </form>
        </div>
      )}

      {loading && <p className="loading-message">Đang tải trang trại…</p>}
      {error && <div className="alert error" role="alert">{error}</div>}
      {!loading && !error && farms.length === 0 && <p>Chưa có trang trại nào.</p>}
      {farms.length > 0 && (
        <table>
          <thead>
            <tr><th>Tên</th><th>Chủ trại</th><th>Tỉnh</th><th>Huyện cũ</th><th>Xã</th><th>Thôn</th><th>Loại</th><th>Quy mô</th><th>Điện thoại</th><th>Email</th><th>Trạng thái</th>{canWrite && <th></th>}</tr>
          </thead>
          <tbody>
            {farms.map((farm) => (
              <tr key={farm.id}>
                <td>{farm.name}</td>
                <td>{farm.owner_name ?? '—'}</td>
                <td>{farm.province}</td>
                <td>{farm.district}</td>
                <td>{farm.commune || '—'}</td>
                <td>{farm.hamlet || '—'}</td>
                <td>{poultryLabel[farm.poultry_type] || farm.poultry_type}</td>
                <td>{farm.capacity}</td>
                <td>{farm.phone ?? '—'}</td>
                <td>{farm.email ?? '—'}</td>
                <td>{farm.is_active ? 'Hoạt động' : 'Ngừng'}</td>
                {canWrite && <td><button className="btn danger" onClick={() => remove(farm)}>Xóa</button></td>}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
