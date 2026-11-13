import { useEffect, useState } from 'react'
import alertService from '../services/alertService'

export default function Dashboard({ onNav }) {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    alertService.all()
      .then(setAlerts)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <h1>Tổng quan</h1>
      {loading && <p>Loading...</p>}
      {!loading && alerts.length === 0 && <p>Chưa có thông báo nào.</p>}
      <div className="grid three">
        {alerts.map((alert) => (
          <div className="card" key={alert.id}>
            <h2>{alert.title}</h2>
            <p>{alert.description}</p>
            <p className="severity" style={{ color: alert.severity === 'Cao' ? '#dc2626' : alert.severity === 'Trung bình' ? '#d97706' : '#16a34a' }}>
              Mức độ: {alert.severity}
            </p>
            <p style={{ fontSize: 12, color: '#64748b' }}>{alert.published_at}</p>
            <button className="btn secondary" style={{ marginTop: 12 }} onClick={() => onNav('alerts')}>Xem chi tiết</button>
          </div>
        ))}
      </div>
    </div>
  )
}