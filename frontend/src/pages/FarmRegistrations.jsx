import { useCallback, useEffect, useState } from 'react'
import MapView from '../components/MapView'
import AddressFields from '../components/AddressFields'
import farmRegistrationService from '../services/farmRegistrationService'
import farmService from '../services/farmService'
import { poultryLabel } from '../utils/labels'

const statusLabel = { pending: 'Đang chờ duyệt', approved: 'Đã chấp thuận', rejected: 'Cần bổ sung thông tin' }
const statusColor = { pending: '#a76318', approved: '#187246', rejected: '#a32b27' }

function newForm(user) {
  return {
    farm_name: '', owner_name: user?.full_name || '', phone: '', email: user?.email || '', address: '',
    province: '', district: '', commune: '', hamlet: '', poultry_type: 'chicken', capacity: 0,
    latitude: '', longitude: '',
  }
}

export default function FarmRegistrations({ user, canReview = false, onNav }) {
  const [records, setRecords] = useState([])
  const [knownAddresses, setKnownAddresses] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [busyId, setBusyId] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState(() => newForm(user))
  const [mapFocus, setMapFocus] = useState(null)
  const [reviewNotes, setReviewNotes] = useState({})

  const load = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true)
    setError('')
    try {
      setRecords(canReview
        ? await farmRegistrationService.pending()
        : await farmRegistrationService.mine())
    } catch (err) {
      setError(err.message)
    } finally {
      if (showLoading) setLoading(false)
    }
  }, [canReview])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    farmService.all()
      .then((farms) => setKnownAddresses(farms.map(({ province, district, commune, hamlet }) => ({ province, district, commune, hamlet }))))
      .catch(() => {})
  }, [])

  const pickedPoint = form.latitude !== '' && form.longitude !== ''
    ? { latitude: Number(form.latitude), longitude: Number(form.longitude) }
    : null
  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }))
  const focusAddress = (focus) => {
    setMapFocus(focus)
    setForm((current) => ({ ...current, latitude: '', longitude: '' }))
  }

  const submit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      await farmRegistrationService.submit({
        farm_name: form.farm_name,
        owner_name: form.owner_name,
        phone: form.phone,
        email: form.email.trim() || null,
        address: form.address.trim() || null,
        province: form.province,
        district: form.district.trim() || null,
        commune: form.commune || null,
        hamlet: form.hamlet.trim() || null,
        poultry_type: form.poultry_type,
        capacity: Number(form.capacity) || 0,
        location: { latitude: Number(form.latitude), longitude: Number(form.longitude) },
      })
      setForm(newForm(user))
      setNotice('Đã gửi hồ sơ đăng ký trại riêng đến cán bộ thú y. Trại chỉ được tạo sau khi được xác nhận.')
      await load(false)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const approve = async (record) => {
    setBusyId(record.id)
    setError('')
    setNotice('')
    try {
      await farmRegistrationService.approve(record.id)
      setRecords((current) => current.filter((item) => item.id !== record.id))
      setNotice(`Đã xác nhận hồ sơ “${record.farm_name}”. Trang trại đã được tạo.`)
    } catch (err) {
      setError(err.message)
      await load(false)
    } finally {
      setBusyId('')
    }
  }

  const reject = async (record) => {
    const review_note = (reviewNotes[record.id] || '').trim()
    if (!review_note) {
      setError(`Vui lòng ghi lý do cần bổ sung cho hồ sơ “${record.farm_name}”.`)
      return
    }
    setBusyId(record.id)
    setError('')
    setNotice('')
    try {
      await farmRegistrationService.reject(record.id, review_note)
      setRecords((current) => current.filter((item) => item.id !== record.id))
      setNotice(`Đã gửi yêu cầu bổ sung cho hồ sơ “${record.farm_name}”.`)
    } catch (err) {
      setError(err.message)
      await load(false)
    } finally {
      setBusyId('')
    }
  }

  const staffView = (
    <>
      <h1>Hồ sơ chờ cán bộ thú y duyệt</h1>
      <p className="map-hint">Hồ sơ đăng ký trại được duyệt riêng; báo cáo dịch bệnh nằm ở mục riêng.</p>
      {loading && <p className="loading-message">Đang tải hồ sơ…</p>}
      {!loading && records.length === 0 && <div className="card"><p>Hiện không có hồ sơ nào đang chờ duyệt.</p></div>}
      {records.map((record) => (
        <article className="card" key={record.id} style={{ marginBottom: 16 }}>
          <h2 style={{ marginTop: 0 }}>{record.farm_name}</h2>
          <div className="grid two">
            <div>
              <p><strong>Chủ trại:</strong> {record.owner_name}</p>
              <p><strong>Điện thoại:</strong> {record.phone}</p>
              <p><strong>Email:</strong> {record.email || '—'}</p>
              <p><strong>Địa chỉ:</strong> {[record.address, record.hamlet, record.commune, record.district, record.province].filter(Boolean).join(', ')}</p>
              <p><strong>Tọa độ:</strong> {record.location.latitude}, {record.location.longitude}</p>
              <p><strong>Đàn gia cầm:</strong> {poultryLabel[record.poultry_type] || record.poultry_type}, {record.capacity.toLocaleString('vi-VN')} con</p>
            </div>
            <div><p><strong>Gửi lúc:</strong> {new Date(record.created_at).toLocaleString('vi-VN')}</p></div>
          </div>
          <label htmlFor={`review-${record.id}`}>Lý do yêu cầu bổ sung (nếu từ chối)</label>
          <textarea
            id={`review-${record.id}`}
            value={reviewNotes[record.id] || ''}
            onChange={(event) => setReviewNotes((current) => ({ ...current, [record.id]: event.target.value }))}
            placeholder="Ghi rõ thông tin cần người gửi bổ sung"
            maxLength={2000}
          />
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 12 }}>
            <button className="btn" type="button" disabled={Boolean(busyId)} onClick={() => approve(record)}>
              {busyId === record.id ? 'Đang xử lý…' : 'Xác nhận và tạo trang trại'}
            </button>
            <button className="btn secondary" type="button" disabled={Boolean(busyId)} onClick={() => reject(record)}>
              Yêu cầu bổ sung
            </button>
          </div>
        </article>
      ))}
    </>
  )

  const ownerView = (
    <>
      <h1>Đăng ký trang trại</h1>
      <p className="map-hint delivery-note">
        Hồ sơ đăng ký được gửi riêng đến cán bộ thú y. Báo cáo dịch bệnh có biểu mẫu riêng ở mục “Báo cáo dịch”.
      </p>
      <div className="card">
        <form onSubmit={submit}>
          <h2>Thông tin trang trại</h2>
          <div className="grid two">
            <div className="field"><label htmlFor="registration-farm-name">Tên trang trại</label><input id="registration-farm-name" value={form.farm_name} onChange={set('farm_name')} maxLength="255" required /></div>
            <div className="field"><label htmlFor="registration-owner">Chủ trại</label><input id="registration-owner" value={form.owner_name} onChange={set('owner_name')} maxLength="255" required /></div>
            <div className="field"><label htmlFor="registration-phone">Số điện thoại</label><input id="registration-phone" type="tel" value={form.phone} onChange={set('phone')} placeholder="0912345678" pattern="(0|\+84)\d{9}" title="Bắt đầu bằng 0 hoặc +84, theo sau là 9 chữ số" required /></div>
            <div className="field"><label htmlFor="registration-email">Email liên hệ nhận cảnh báo</label><input id="registration-email" type="email" value={form.email} onChange={set('email')} /></div>
            <AddressFields
              value={form}
              knownAddresses={knownAddresses}
              idPrefix="registration"
              onLocationFocus={focusAddress}
              onChange={(address) => setForm((current) => ({ ...current, ...address }))}
            />
            <div className="field"><label htmlFor="registration-address">Số nhà, đường / địa chỉ chi tiết</label><input id="registration-address" value={form.address} onChange={set('address')} /></div>
            <div className="field">
              <label htmlFor="registration-poultry">Loại gia cầm</label>
              <select id="registration-poultry" value={form.poultry_type} onChange={set('poultry_type')}>
                {Object.entries(poultryLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </div>
            <div className="field"><label htmlFor="registration-capacity">Tổng đàn (con)</label><input id="registration-capacity" type="number" min="0" value={form.capacity} onChange={set('capacity')} /></div>
            <div className="field"><label htmlFor="registration-latitude">Vĩ độ</label><input id="registration-latitude" type="number" step="any" min="-90" max="90" value={form.latitude} onChange={set('latitude')} required /></div>
            <div className="field"><label htmlFor="registration-longitude">Kinh độ</label><input id="registration-longitude" type="number" step="any" min="-180" max="180" value={form.longitude} onChange={set('longitude')} required /></div>
          </div>
          <p className="map-hint">Chọn vị trí trang trại trên bản đồ để điền tọa độ.</p>
          <div className="picker large-square-map-picker"><MapView height="100%" picked={pickedPoint} focus={mapFocus} onPick={(point) => setForm((current) => ({ ...current, latitude: String(point.latitude), longitude: String(point.longitude) }))} /></div>
          <button className="btn" type="submit" disabled={saving}>{saving ? 'Đang gửi hồ sơ…' : 'Gửi cán bộ thú y xét duyệt'}</button>
        </form>
      </div>

      <h2>Hồ sơ của tôi</h2>
      {loading && <p className="loading-message">Đang tải trạng thái hồ sơ…</p>}
      {!loading && records.length === 0 && <p>Bạn chưa gửi hồ sơ đăng ký trại nào.</p>}
      {records.map((record) => (
        <article className="card" key={record.id} style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 14, flexWrap: 'wrap' }}>
            <strong>{record.farm_name}</strong>
            <strong style={{ color: statusColor[record.status] }}>{statusLabel[record.status] || record.status}</strong>
          </div>
          <p className="map-hint">Gửi lúc {new Date(record.created_at).toLocaleString('vi-VN')}</p>
          {record.status === 'rejected' && record.review_note && <p className="alert error" role="status">Cán bộ thú y yêu cầu: {record.review_note}</p>}
          {record.status === 'approved' && <button className="btn secondary" type="button" onClick={() => onNav?.('farms')}>Xem trang trại đã đăng ký</button>}
        </article>
      ))}
    </>
  )

  return (
    <div className="page">
      {error && <div className="alert error" role="alert">{error}</div>}
      {notice && <div className="alert success" role="status">{notice}</div>}
      {canReview ? staffView : ownerView}
    </div>
  )
}
