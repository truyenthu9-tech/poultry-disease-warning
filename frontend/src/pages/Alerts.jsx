import { useEffect, useState } from 'react'
import alertService from '../services/alertService'
import AlertCard from '../components/AlertCard'

export default function Alerts({ canWrite = false }) {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = () => {
    setError('')
    return alertService.all()
      .then(setAlerts)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const acknowledge = async (id) => {
    try {
      const updated = await alertService.acknowledge(id)
      setAlerts((list) => list.map((a) => (a.id === id ? updated : a)))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page">
      <h1>Thông báo</h1>
      {!canWrite && (
        <p className="map-hint">Bạn chỉ thấy cảnh báo của trang trại được gán cho tài khoản của mình.</p>
      )}
      {loading && <p className="loading-message">Đang tải thông báo…</p>}
      {error && <div className="alert error" role="alert">{error}</div>}
      {!loading && !error && alerts.length === 0 && (
        canWrite
          ? <p>Chưa có thông báo nào. Vào trang Bùng phát bệnh, xác nhận ổ dịch rồi bấm "Tạo cảnh báo" ở ổ dịch đang hoạt động.</p>
          : <p>Chưa có thông báo nào cho trang trại của bạn. Nếu bạn là chủ trại, hãy nhờ cán bộ thú y gán trang trại cho tài khoản này.</p>
      )}
      <div className="grid three">
        {alerts.map((alert) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            actionLabel={alert.status === 'acknowledged' ? undefined : 'Xác nhận đã biết'}
            onAction={alert.status === 'acknowledged' ? undefined : () => acknowledge(alert.id)}
          />
        ))}
      </div>
    </div>
  )
}
