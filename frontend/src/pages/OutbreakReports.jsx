import { useCallback, useEffect, useState } from 'react'
import AddressFields from '../components/AddressFields'
import MapView from '../components/MapView'
import farmService from '../services/farmService'
import outbreakReportService from '../services/outbreakReportService'
import { formatDate } from '../utils/labels'

const statusLabel = { pending: 'Đang chờ cán bộ thú y xác nhận', approved: 'Đã xác nhận', rejected: 'Cần bổ sung thông tin' }
const statusColor = { pending: '#a76318', approved: '#187246', rejected: '#a32b27' }

function newForm(user) {
  return {
    reporter_name: user?.full_name || '', phone: '', virus_type: 'Nghi mắc cúm gia cầm',
    province: '', district: '', commune: '', hamlet: '', address: '',
    onset_date: '', cases_count: 1, description: '', latitude: '', longitude: '',
  }
}

function localDateTimeNow() {
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  return now.toISOString().slice(0, 16)
}

export default function OutbreakReports({ user, canReview = false }) {
  const [records, setRecords] = useState([])
  const [knownAddresses, setKnownAddresses] = useState([])
  const [form, setForm] = useState(() => ({ ...newForm(user), onset_date: localDateTimeNow() }))
  const [reviewNotes, setReviewNotes] = useState({})
  const [mapFocus, setMapFocus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [busyId, setBusyId] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const load = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true)
    setError('')
    try {
      setRecords(canReview ? await outbreakReportService.pending() : await outbreakReportService.mine())
    } catch (err) {
      setError(err.message)
    } finally {
      if (showLoading) setLoading(false)
    }
  }, [canReview])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    farmService.all()
      .then((farms) => setKnownAddresses(farms.map(({ province, commune, hamlet }) => ({ province, commune, hamlet }))))
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
      await outbreakReportService.submit({
        reporter_name: form.reporter_name.trim(),
        phone: form.phone.trim(),
        virus_type: form.virus_type.trim(),
        province: form.province,
        district: form.district.trim() || null,
        commune: form.commune || null,
        hamlet: form.hamlet.trim() || null,
        address: form.address.trim() || null,
        onset_date: new Date(form.onset_date).toISOString(),
        cases_count: Number(form.cases_count),
        description: form.description.trim() || null,
        location: { latitude: Number(form.latitude), longitude: Number(form.longitude) },
      })
      setForm({ ...newForm(user), onset_date: localDateTimeNow() })
      setMapFocus(null)
      setNotice('Đã gửi báo cáo riêng đến cán bộ thú y. Báo cáo chưa xuất hiện trên bản đồ dịch bệnh cho đến khi được xác nhận.')
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
      await outbreakReportService.approve(record.id)
      setRecords((current) => current.filter((item) => item.id !== record.id))
      setNotice(`Đã xác nhận báo cáo tại ${[record.hamlet, record.commune, record.province].filter(Boolean).join(', ')}; ổ dịch đã được tạo.`)
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
      setError('Vui lòng ghi lý do yêu cầu bổ sung thông tin.')
      return
    }
    setBusyId(record.id)
    setError('')
    setNotice('')
    try {
      await outbreakReportService.reject(record.id, review_note)
      setRecords((current) => current.filter((item) => item.id !== record.id))
      setNotice('Đã gửi yêu cầu bổ sung cho người báo cáo.')
    } catch (err) {
      setError(err.message)
      await load(false)
    } finally {
      setBusyId('')
    }
  }

  const ownerView = (
    <>
      <h1>Báo cáo dịch bệnh</h1>
      <p className="map-hint delivery-note">
        Báo cáo dịch bệnh độc lập với đăng ký trang trại. Thông tin được gửi riêng cho cán bộ thú y; chỉ sau khi xác nhận mới tạo ổ dịch công khai.
      </p>
      <div className="card">
        <form onSubmit={submit}>
          <h2>Thông tin người báo cáo</h2>
          <div className="grid two">
            <div className="field"><label htmlFor="reporter-name">Họ tên</label><input id="reporter-name" value={form.reporter_name} onChange={set('reporter_name')} maxLength="255" required /></div>
            <div className="field"><label htmlFor="reporter-phone">Số điện thoại</label><input id="reporter-phone" type="tel" value={form.phone} onChange={set('phone')} placeholder="0912345678" pattern="(0|\+84)\d{9}" title="Bắt đầu bằng 0 hoặc +84, theo sau là 9 chữ số" required /></div>
          </div>
          <h2>Địa điểm ổ dịch</h2>
          <div className="grid two">
            <AddressFields
              value={form}
              knownAddresses={knownAddresses}
              idPrefix="outbreak-report"
              onLocationFocus={focusAddress}
              onChange={(address) => setForm((current) => ({ ...current, ...address }))}
            />
            <div className="field"><label htmlFor="report-address">Địa chỉ chi tiết / tên trại</label><input id="report-address" value={form.address} onChange={set('address')} maxLength="1000" placeholder="Ví dụ: khu chuồng số 2" /></div>
            <div className="field"><label htmlFor="report-latitude">Vĩ độ</label><input id="report-latitude" type="number" step="any" min="-90" max="90" value={form.latitude} onChange={set('latitude')} required /></div>
            <div className="field"><label htmlFor="report-longitude">Kinh độ</label><input id="report-longitude" type="number" step="any" min="-180" max="180" value={form.longitude} onChange={set('longitude')} required /></div>
          </div>
          <p className="map-hint">Chọn tỉnh rồi xã để bản đồ tự phóng đến khu vực đó; bấm lên bản đồ để ghim chính xác vị trí phát bệnh.</p>
          <div className="picker large-square-map-picker">
            <MapView
              height="100%"
              focus={mapFocus}
              picked={pickedPoint}
              onPick={(point) => setForm((current) => ({ ...current, latitude: String(point.latitude), longitude: String(point.longitude) }))}
            />
          </div>

          <h2 style={{ marginTop: 24 }}>Thông tin dịch bệnh</h2>
          <div className="grid two">
            <div className="field"><label htmlFor="report-virus">Bệnh / tác nhân nghi ngờ</label><input id="report-virus" value={form.virus_type} onChange={set('virus_type')} maxLength="255" required /></div>
            <div className="field"><label htmlFor="report-onset">Thời gian bắt đầu phát bệnh</label><input id="report-onset" type="datetime-local" value={form.onset_date} onChange={set('onset_date')} required /></div>
            <div className="field"><label htmlFor="report-cases">Số gia cầm nhiễm bệnh</label><input id="report-cases" type="number" min="1" step="1" value={form.cases_count} onChange={set('cases_count')} required /></div>
            <div className="field"><label htmlFor="report-description">Mô tả thêm</label><textarea id="report-description" value={form.description} onChange={set('description')} maxLength="4000" /></div>
          </div>
          <button className="btn" type="submit" disabled={saving}>{saving ? 'Đang gửi báo cáo…' : 'Gửi cán bộ thú y xác nhận'}</button>
        </form>
      </div>

      <h2>Báo cáo của tôi</h2>
      {loading && <p className="loading-message">Đang tải báo cáo…</p>}
      {!loading && records.length === 0 && <p>Bạn chưa gửi báo cáo dịch bệnh nào.</p>}
      {records.map((record) => (
        <article className="card" key={record.id} style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 14, flexWrap: 'wrap' }}>
            <strong>{record.virus_type} · {record.cases_count.toLocaleString('vi-VN')} con nhiễm</strong>
            <strong style={{ color: statusColor[record.status] }}>{statusLabel[record.status] || record.status}</strong>
          </div>
          <p>{[record.hamlet, record.commune, record.province].filter(Boolean).join(', ')} · bắt đầu {formatDate(record.onset_date)}</p>
          <p className="map-hint">Gửi lúc {formatDate(record.created_at)}</p>
          {record.status === 'rejected' && record.review_note && <p className="alert error" role="status">Cán bộ thú y yêu cầu: {record.review_note}</p>}
        </article>
      ))}
    </>
  )

  const staffView = (
    <>
      <h1>Báo cáo dịch bệnh chờ xác nhận</h1>
      <p className="map-hint">Ổ dịch chỉ được đưa lên bản đồ và dùng cho cảnh báo sau khi cán bộ thú y xác nhận.</p>
      {loading && <p className="loading-message">Đang tải báo cáo…</p>}
      {!loading && records.length === 0 && <div className="card"><p>Hiện không có báo cáo nào đang chờ xác nhận.</p></div>}
      {records.map((record) => (
        <article className="card" key={record.id} style={{ marginBottom: 16 }}>
          <h2 style={{ marginTop: 0 }}>{record.virus_type} · {record.cases_count.toLocaleString('vi-VN')} con nhiễm</h2>
          <div className="grid two">
            <div>
              <p><strong>Người báo cáo:</strong> {record.reporter_name}</p>
              <p><strong>Điện thoại:</strong> {record.phone}</p>
              <p><strong>Địa chỉ:</strong> {[record.address, record.hamlet, record.commune, record.district, record.province].filter(Boolean).join(', ')}</p>
              <p><strong>Tọa độ:</strong> {record.location.latitude}, {record.location.longitude}</p>
            </div>
            <div>
              <p><strong>Bắt đầu phát bệnh:</strong> {formatDate(record.onset_date)}</p>
              {record.description && <p><strong>Mô tả:</strong> {record.description}</p>}
              <p><strong>Gửi lúc:</strong> {formatDate(record.created_at)}</p>
            </div>
          </div>
          <label htmlFor={`report-review-${record.id}`}>Lý do yêu cầu bổ sung (nếu từ chối)</label>
          <textarea
            id={`report-review-${record.id}`}
            value={reviewNotes[record.id] || ''}
            onChange={(event) => setReviewNotes((current) => ({ ...current, [record.id]: event.target.value }))}
            placeholder="Ghi rõ thông tin cần người gửi bổ sung"
            maxLength={2000}
          />
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 12 }}>
            <button className="btn" type="button" disabled={Boolean(busyId)} onClick={() => approve(record)}>
              {busyId === record.id ? 'Đang xử lý…' : 'Xác nhận và tạo ổ dịch'}
            </button>
            <button className="btn secondary" type="button" disabled={Boolean(busyId)} onClick={() => reject(record)}>
              Yêu cầu bổ sung
            </button>
          </div>
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
