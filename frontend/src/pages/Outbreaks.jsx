import { useEffect, useState } from 'react'
import MapView, { MapLegend } from '../components/MapView'
import AddressFields from '../components/AddressFields'
import outbreakService from '../services/outbreakService'
import alertService from '../services/alertService'
import farmService from '../services/farmService'
import { alertStatusLabel, formatDate, outbreakStatusLabel, riskColor, riskLabel, sourceLabel } from '../utils/labels'

const emptyForm = {
  virus_type: 'H5N1', province: '', district: '', commune: '', hamlet: '', cases_count: 0,
  severity: 'medium', status: 'active', radius_km: 5, latitude: '', longitude: '',
}

export default function Outbreaks({ onNav, canWrite = false }) {
  const [outbreaks, setOutbreaks] = useState([])
  const [knownAddresses, setKnownAddresses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [mapFocus, setMapFocus] = useState(null)
  const [saving, setSaving] = useState(false)
  const [importing, setImporting] = useState(false)

  const load = () => outbreakService.all()
    .then(setOutbreaks)
    .catch((err) => setError(err.message))
    .finally(() => setLoading(false))

  useEffect(() => { load() }, [])
  useEffect(() => {
    farmService.all()
      .then((farms) => setKnownAddresses(farms.map(({ province, district, commune, hamlet }) => ({ province, district, commune, hamlet }))))
      .catch(() => {})
  }, [])

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
    setNotice('')
    try {
      await outbreakService.create({
        virus_type: form.virus_type,
        province: form.province,
        district: form.district || null,
        commune: form.commune || null,
        hamlet: form.hamlet.trim() || null,
        cases_count: Number(form.cases_count) || 0,
        severity: form.severity,
        status: form.status,
        radius_km: Number(form.radius_km) || null,
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

  const generateAlerts = async (outbreak) => {
    setError('')
    setNotice('')
    try {
      const previous = await alertService.forOutbreak(outbreak.id)
      const previousIds = new Set(previous.map((alert) => alert.id))
      const results = await alertService.generateForOutbreak(outbreak.id)
      const created = results.filter((alert) => !previousIds.has(alert.id))
      const updated = results.filter((alert) => previousIds.has(alert.id))

      if (created.length > 0 || updated.length > 0) {
        const changes = []
        if (created.length > 0) changes.push(`đã tạo ${created.length} cảnh báo mới`)
        if (updated.length > 0) {
          const levels = [...new Set(updated.map((alert) => riskLabel[alert.risk_level] || alert.risk_level))]
          changes.push(`đã cập nhật ${updated.length} cảnh báo cũ lên mức ${levels.join(', ')}`)
        }
        setNotice(`Hệ thống ${changes.join(' và ')} trong bán kính ${outbreak.radius_km} km. Xem mục Thông báo để kiểm tra mức hiện tại.`)
        return
      }

      if (previous.length > 0) {
        const statuses = [...new Set(previous.map((alert) => alertStatusLabel[alert.status] || alert.status))]
        setNotice(`Ổ dịch này đã có ${previous.length} cảnh báo (${statuses.join(', ')}), hiện không có mức nào cần cập nhật. Hệ thống không tạo hoặc gửi lặp thông báo. Xem mục Thông báo để kiểm tra chi tiết.`)
      } else {
        setNotice(`Không có trang trại nào trong bán kính ${outbreak.radius_km} km của ổ dịch này.`)
      }
    } catch (err) {
      setError(err.message)
    }
  }

  const verify = async (outbreak) => {
    if (!window.confirm(`Xác nhận ổ dịch ${outbreak.virus_type} tại ${outbreak.province} là có thật và thông tin đã đúng? Sau khi xác nhận mới tạo được cảnh báo.`)) return
    setError('')
    setNotice('')
    try {
      const updated = await outbreakService.verify(outbreak.id)
      setOutbreaks((list) => list.map((o) => (o.id === updated.id ? updated : o)))
    } catch (err) {
      setError(err.message)
    }
  }

  const importFromSources = async () => {
    setError('')
    setNotice('')
    setImporting(true)
    try {
      const r = await outbreakService.importFromSources()
      setNotice(
        r.sources_configured === 0
          ? 'Chưa cấu hình nguồn dữ liệu nào (OUTBREAK_FEED_URLS) nên không có gì để nhập.'
          : `Đã nhập ${r.created} ổ dịch mới ở trạng thái chưa xác nhận, bỏ qua ${r.duplicates} bản ghi trùng, ${r.invalid} bản ghi không hợp lệ.${r.errors.length ? ` Lỗi: ${r.errors.join('; ')}` : ''}`
      )
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setImporting(false)
    }
  }

  const remove = async (outbreak) => {
    if (!window.confirm(`Xóa ổ dịch ${outbreak.virus_type} tại ${outbreak.province}?`)) return
    try {
      await outbreakService.remove(outbreak.id)
      setOutbreaks((list) => list.filter((o) => o.id !== outbreak.id))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page">
      <h1>Bùng phát bệnh</h1>
      {canWrite
        ? (
          <p>
            <button className="btn" onClick={() => setShowForm(!showForm)}>{showForm ? 'Đóng form' : 'Thêm ổ dịch'}</button>{' '}
            <button className="btn secondary" onClick={importFromSources} disabled={importing}>
              {importing ? 'Đang nhập...' : 'Nhập từ nguồn dữ liệu'}
            </button>
          </p>
        )
        : <p className="map-hint">Bạn chỉ có quyền xem. Việc thêm ổ dịch và tạo cảnh báo dành cho quản trị viên và cán bộ thú y.</p>}

      {canWrite && <p className="map-hint delivery-note">Cảnh báo được lưu trong mục Thông báo. Email chỉ được gửi khi trang trại có địa chỉ email và máy chủ đã cấu hình SMTP.</p>}

      {canWrite && showForm && (
        <div className="card">
          <form onSubmit={handleSubmit}>
            <div className="grid two">
              <div className="field"><label htmlFor="outbreak-virus">Loại virus</label><input id="outbreak-virus" value={form.virus_type} onChange={set('virus_type')} required /></div>
              <div className="field"><label htmlFor="outbreak-cases">Số ca</label><input id="outbreak-cases" type="number" min="0" value={form.cases_count} onChange={set('cases_count')} /></div>
              <AddressFields
                value={form}
                knownAddresses={knownAddresses}
                idPrefix="outbreak"
                onLocationFocus={focusAddress}
                onChange={(address) => setForm((current) => ({ ...current, ...address }))}
              />
              <div className="field">
                <label htmlFor="outbreak-severity">Mức độ</label>
                <select id="outbreak-severity" value={form.severity} onChange={set('severity')}>
                  {Object.entries(riskLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </div>
              <div className="field">
                <label htmlFor="outbreak-status">Trạng thái</label>
                <select id="outbreak-status" value={form.status} onChange={set('status')}>
                  {Object.entries(outbreakStatusLabel).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </div>
              <div className="field"><label htmlFor="outbreak-radius">Bán kính cảnh báo (km)</label><input id="outbreak-radius" type="number" step="any" min="0.1" value={form.radius_km} onChange={set('radius_km')} /></div>
              <div />
              <div className="field"><label htmlFor="outbreak-latitude">Vĩ độ (latitude)</label><input id="outbreak-latitude" type="number" step="any" min="-90" max="90" value={form.latitude} onChange={set('latitude')} placeholder="21.17" required /></div>
              <div className="field"><label htmlFor="outbreak-longitude">Kinh độ (longitude)</label><input id="outbreak-longitude" type="number" step="any" min="-180" max="180" value={form.longitude} onChange={set('longitude')} placeholder="105.848" required /></div>
            </div>
            <p className="map-hint">Bấm lên bản đồ để chọn vị trí ổ dịch, vĩ độ và kinh độ sẽ tự điền.</p>
            <div className="picker">
              <MapView
                height={320}
                outbreaks={outbreaks}
                picked={pickedPoint}
                focus={mapFocus}
                onPick={(p) => setForm((f) => ({ ...f, latitude: String(p.latitude), longitude: String(p.longitude) }))}
              />
            </div>
            <button className="btn" type="submit" disabled={saving} style={{ marginTop: 12 }}>Lưu ổ dịch</button>
          </form>
        </div>
      )}

      {loading && <p className="loading-message">Đang tải dữ liệu ổ dịch…</p>}
      {error && <div className="alert error" role="alert">{error}</div>}
      {notice && (
        <div className="alert success" role="status">
          {notice} <a href="#alerts" onClick={(e) => { e.preventDefault(); onNav?.('alerts') }}>Xem thông báo</a>
        </div>
      )}
      {!loading && !error && outbreaks.length === 0 && <p>Chưa có bùng phát nào.</p>}
      {outbreaks.length > 0 && (
        <>
          <MapLegend />
          <MapView height={360} outbreaks={outbreaks} />
          <div style={{ height: 16 }} />
        </>
      )}
      {outbreaks.length > 0 && (
        <table>
          <thead>
            <tr><th>Virus</th><th>Tỉnh</th><th>Huyện cũ</th><th>Xã</th><th>Thôn</th><th>Số ca</th><th>Bán kính (km)</th><th>Mức độ</th><th>Trạng thái</th><th>Bắt đầu phát bệnh</th><th>Nguồn</th><th>Xác nhận</th>{canWrite && <th></th>}</tr>
          </thead>
          <tbody>
            {outbreaks.map((o) => (
              <tr key={o.id}>
                <td>{o.virus_type}</td>
                <td>{o.province}</td>
                <td>{o.district}</td>
                <td>{o.commune || '—'}</td>
                <td>{o.hamlet || '—'}</td>
                <td>{o.cases_count}</td>
                <td>{o.radius_km}</td>
                <td style={{ color: riskColor[o.severity], fontWeight: 600 }}>{riskLabel[o.severity] || o.severity}</td>
                <td>{outbreakStatusLabel[o.status] || o.status}</td>
                <td>{formatDate(o.onset_date || o.reported_date)}</td>
                <td>{sourceLabel(o.source)}</td>
                <td style={{ color: o.verified ? '#16a34a' : '#d97706', fontWeight: 600 }}>{o.verified ? 'Đã xác nhận' : 'Chưa xác nhận'}</td>
                {canWrite && (
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {!o.verified && <button className="btn" onClick={() => verify(o)}>Xác nhận</button>}{' '}
                    {o.verified && o.status === 'active' && <button className="btn secondary" onClick={() => generateAlerts(o)}>Tạo / cập nhật cảnh báo</button>}{' '}
                    <button className="btn danger" onClick={() => remove(o)}>Xóa</button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
