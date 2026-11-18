import { advisoryNotice, alertStatusLabel, formatDate, riskColor, riskLabel } from '../utils/labels'

export default function AlertCard({ alert, actionLabel, onAction }) {
  return (
    <div className="card">
      <h2>Cảnh báo {riskLabel[alert.risk_level] || alert.risk_level}</h2>
      <p>{alert.message}</p>
      <p className="severity" style={{ color: riskColor[alert.risk_level] }}>
        Mức độ: {riskLabel[alert.risk_level] || alert.risk_level} · Cách ổ dịch {alert.distance_km} km
      </p>
      {alert.risk_basis && (
        <p style={{ fontSize: 12, color: '#475569' }}>Cơ sở đánh giá: {alert.risk_basis}</p>
      )}
      <p style={{ fontSize: 12, color: '#64748b' }}>
        {alertStatusLabel[alert.status] || alert.status} · {formatDate(alert.created_at)}
      </p>
      <p style={{ fontSize: 12, color: '#64748b', fontStyle: 'italic' }}>{advisoryNotice}</p>
      {onAction && <button className="btn secondary" style={{ marginTop: 12 }} onClick={onAction}>{actionLabel}</button>}
    </div>
  )
}
