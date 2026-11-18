import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import alertService from '../services/alertService'
import farmService from '../services/farmService'
import outbreakService from '../services/outbreakService'
import Icon from '../components/Icon'
import { formatDate, outbreakStatusLabel, riskLabel } from '../utils/labels'

const numberFormat = new Intl.NumberFormat('vi-VN')
const severityRank = { low: 1, medium: 2, high: 3, critical: 4 }
const statusFilters = [
  { value: 'all', label: 'Tất cả' },
  { value: 'active', label: 'Đang hoạt động' },
  { value: 'contained', label: 'Đã khống chế' },
  { value: 'closed', label: 'Đã đóng' },
]

function hasLocation(location) {
  return location
    && location.latitude !== null && location.latitude !== ''
    && location.longitude !== null && location.longitude !== ''
    && Number.isFinite(Number(location.latitude))
    && Number.isFinite(Number(location.longitude))
}

function distanceKm(a, b) {
  const radians = (degrees) => (degrees * Math.PI) / 180
  const lat1 = radians(Number(a.latitude))
  const lat2 = radians(Number(b.latitude))
  const deltaLat = lat2 - lat1
  const deltaLon = radians(Number(b.longitude) - Number(a.longitude))
  const arc = Math.sin(deltaLat / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLon / 2) ** 2
  const boundedArc = Math.min(1, Math.max(0, arc))
  return 6371 * 2 * Math.atan2(Math.sqrt(boundedArc), Math.sqrt(1 - boundedArc))
}

function findExposure(farms, outbreaks, alerts) {
  const trackedFarms = farms.filter((farm) => farm.is_active !== false && hasLocation(farm.location))
  const alertByPair = new Map(alerts.map((item) => [`${item.farm_id}:${item.outbreak_id}`, item]))
  const matches = []

  trackedFarms.forEach((farm) => {
    outbreaks.forEach((outbreak) => {
      if (outbreak.status !== 'active' || !outbreak.verified || !hasLocation(outbreak.location)) return
      const distance = distanceKm(farm.location, outbreak.location)
      if (distance <= Number(outbreak.radius_km || 0)) {
        const alert = alertByPair.get(`${farm.id}:${outbreak.id}`)
        matches.push({ farm, outbreak, distance, riskLevel: alert?.risk_level || outbreak.severity })
      }
    })
  })

  const affectedFarmIds = new Set(matches.map(({ farm }) => farm.id))
  const highestMatch = [...matches].sort((a, b) => (
    (severityRank[b.riskLevel] || 0) - (severityRank[a.riskLevel] || 0)
    || a.distance - b.distance
  ))[0]

  return { trackedFarms, affectedFarmIds, highestMatch, matches }
}

function buildMonthlyTrend(outbreaks) {
  const now = new Date()
  const months = Array.from({ length: 6 }, (_, index) => {
    const date = new Date(now.getFullYear(), now.getMonth() - (5 - index), 1)
    return { date, key: `${date.getFullYear()}-${date.getMonth()}`, count: 0 }
  })
  const monthMap = new Map(months.map((month) => [month.key, month]))

  outbreaks.forEach((outbreak) => {
    if (!outbreak.verified || !outbreak.reported_date) return
    const date = new Date(outbreak.reported_date)
    if (Number.isNaN(date.getTime())) return
    const key = `${date.getFullYear()}-${date.getMonth()}`
    const month = monthMap.get(key)
    if (month) month.count += 1
  })

  return months
}

function TrendChart({ months }) {
  const width = 660
  const plot = { left: 38, right: 638, top: 18, bottom: 168 }
  const maximum = Math.max(1, ...months.map((month) => month.count))
  const points = months.map((month, index) => {
    const x = plot.left + (index * (plot.right - plot.left)) / Math.max(months.length - 1, 1)
    const y = plot.bottom - (month.count / maximum) * (plot.bottom - plot.top - 12)
    return { ...month, x, y }
  })
  const line = points.map(({ x, y }) => `${x},${y}`).join(' ')
  const area = `${plot.left},${plot.bottom} ${line} ${plot.right},${plot.bottom}`
  const labelFormat = new Intl.DateTimeFormat('vi-VN', { month: 'short' })

  return (
    <svg className="trend-chart" viewBox={`0 0 ${width} 220`} role="img" aria-label="Số ổ dịch đã xác nhận trong sáu tháng gần đây">
      {[0, 0.5, 1].map((fraction) => {
        const y = plot.bottom - fraction * (plot.bottom - plot.top - 12)
        return (
          <g key={fraction}>
            <line x1={plot.left} x2={plot.right} y1={y} y2={y} className="chart-grid-line" />
            <text x="27" y={y + 4} className="chart-axis-label" textAnchor="end">
              {Math.round(maximum * fraction)}
            </text>
          </g>
        )
      })}
      <polygon points={area} className="chart-area" />
      <polyline points={line} className="chart-line" />
      {points.map((point) => (
        <g key={point.key}>
          <circle cx={point.x} cy={point.y} r="4.5" className="chart-point" />
          <text x={point.x} y="198" className="chart-month-label" textAnchor="middle">
            {labelFormat.format(point.date).replace('.', '')}
          </text>
        </g>
      ))}
    </svg>
  )
}

function SeverityBreakdown({ outbreaks }) {
  const levels = ['critical', 'high', 'medium', 'low']
  const counts = Object.fromEntries(levels.map((level) => [
    level,
    outbreaks.filter((outbreak) => outbreak.severity === level).length,
  ]))
  const maxCount = Math.max(1, ...Object.values(counts))

  return (
    <div className="severity-list">
      {levels.map((level) => (
        <div className="severity-row" key={level}>
          <div className="severity-row-heading">
            <span className={`severity-dot severity-dot--${level}`} aria-hidden="true" />
            <span>{riskLabel[level]}</span>
            <strong>{numberFormat.format(counts[level])}</strong>
          </div>
          <div
            className="severity-track"
            role="img"
            aria-label={`${riskLabel[level]}: ${numberFormat.format(counts[level])} ổ dịch`}
          >
            <span
              className={`severity-fill severity-fill--${level}`}
              style={{ width: `${(counts[level] / maxCount) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

function getAreaStatus(exposure) {
  if (exposure.trackedFarms.length === 0) {
    return {
      level: 'unknown',
      eyebrow: 'CHƯA CÓ VÙNG THEO DÕI',
      title: 'Chưa có vị trí trang trại để đối chiếu',
      description: 'Thêm hoặc gán một trang trại có tọa độ để kiểm tra cảnh báo quanh khu vực.',
    }
  }

  if (!exposure.highestMatch) {
    return {
      level: 'clear',
      eyebrow: 'CHƯA GHI NHẬN Ổ DỊCH GẦN ĐÂY',
      title: 'Chưa có ổ dịch trong bán kính cảnh báo',
      description: 'Các trang trại có tọa độ hiện không nằm trong vùng bán kính của ổ dịch đang hoạt động đã xác nhận.',
    }
  }

  const severity = exposure.highestMatch.riskLevel || 'medium'
  const copy = {
    low: ['CẢNH BÁO NHẸ', 'Có ổ dịch mức nhẹ trong khu vực'],
    medium: ['CẢNH BÁO TRUNG BÌNH', 'Có ổ dịch mức trung bình trong khu vực'],
    high: ['CẢNH BÁO NGUY HIỂM', 'Trang trại nằm trong vùng dịch nguy hiểm'],
    critical: ['CẢNH BÁO NGHIÊM TRỌNG', 'Trang trại nằm trong vùng dịch nghiêm trọng'],
  }[severity] || ['CẢNH BÁO TRUNG BÌNH', 'Có ổ dịch trong khu vực']

  return {
    level: severity,
    eyebrow: copy[0],
    title: copy[1],
    description: `${exposure.affectedFarmIds.size} trang trại nằm trong vùng ảnh hưởng. Ổ dịch gần nhất: ${exposure.highestMatch.outbreak.virus_type} · ${[exposure.highestMatch.outbreak.hamlet, exposure.highestMatch.outbreak.commune, exposure.highestMatch.outbreak.district, exposure.highestMatch.outbreak.province].filter(Boolean).join(', ') || 'Chưa rõ địa điểm'} · cách ${exposure.highestMatch.distance.toFixed(1)} km.`,
  }
}

function MetricCard({ label, value, detail, icon, tone = 'green' }) {
  return (
    <div className="metric-card">
      <div className={`metric-icon metric-icon--${tone}`}><Icon name={icon} size={19} /></div>
      <div className="metric-copy">
        <span>{label}</span>
        <strong>{numberFormat.format(value)}</strong>
        <small>{detail}</small>
      </div>
    </div>
  )
}

export default function Dashboard({ onNav, user }) {
  const [data, setData] = useState({ alerts: [], farms: [], outbreaks: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const requestInFlight = useRef(false)
  const isStaff = ['admin', 'vet_officer'].includes(user?.role)

  const load = useCallback(async () => {
    if (requestInFlight.current) return
    requestInFlight.current = true
    setLoading(true)
    setError('')
    try {
      const farmRequest = isStaff ? farmService.all() : farmService.mine()
      const [alerts, farms, outbreaks] = await Promise.all([
        alertService.all(), farmRequest, outbreakService.all(),
      ])
      setData({ alerts, farms, outbreaks })
      setLastUpdated(new Date())
    } catch (err) {
      setError(err.message || 'Không thể tải dữ liệu tổng quan.')
    } finally {
      requestInFlight.current = false
      setLoading(false)
    }
  }, [isStaff])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    if (!autoRefresh) return undefined
    const interval = window.setInterval(() => {
      if (document.visibilityState === 'visible') load()
    }, 60_000)
    return () => window.clearInterval(interval)
  }, [autoRefresh, load])

  const verifiedOutbreaks = useMemo(
    () => data.outbreaks.filter((outbreak) => outbreak.verified),
    [data.outbreaks],
  )
  const activeOutbreaks = useMemo(
    () => verifiedOutbreaks.filter((outbreak) => outbreak.status === 'active'),
    [verifiedOutbreaks],
  )
  const exposure = useMemo(
    () => findExposure(data.farms, activeOutbreaks, data.alerts),
    [data.farms, activeOutbreaks, data.alerts],
  )
  const areaStatus = getAreaStatus(exposure)
  const monthlyTrend = useMemo(() => buildMonthlyTrend(verifiedOutbreaks), [verifiedOutbreaks])
  const severityTotal = Object.values({
    low: verifiedOutbreaks.filter((outbreak) => outbreak.severity === 'low').length,
    medium: verifiedOutbreaks.filter((outbreak) => outbreak.severity === 'medium').length,
    high: verifiedOutbreaks.filter((outbreak) => outbreak.severity === 'high').length,
    critical: verifiedOutbreaks.filter((outbreak) => outbreak.severity === 'critical').length,
  }).reduce((sum, count) => sum + count, 0)
  const reportedCases = verifiedOutbreaks.reduce((sum, outbreak) => sum + (Number(outbreak.cases_count) || 0), 0)
  const resolvedCount = verifiedOutbreaks.filter((outbreak) => outbreak.status === 'contained' || outbreak.status === 'closed').length
  const visibleOutbreaks = useMemo(() => data.outbreaks
    .filter((outbreak) => statusFilter === 'all' || outbreak.status === statusFilter)
    .slice(0, 6), [data.outbreaks, statusFilter])

  const isLoadingInitial = loading && !lastUpdated

  return (
    <div className="page dashboard-page" data-risk-level={areaStatus.level}>
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">TRUNG TÂM GIÁM SÁT</p>
          <h1>Tổng quan ổ dịch</h1>
          <p className="dashboard-subtitle">Theo dõi tình hình dịch bệnh gia cầm và mức cảnh báo quanh trang trại.</p>
        </div>
        <div className="dashboard-tools">
          <span className="update-label">
            <span className={`status-pulse ${autoRefresh ? '' : 'status-pulse--paused'}`} aria-hidden="true" />
            {lastUpdated ? `Cập nhật ${lastUpdated.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}` : 'Chưa đồng bộ'}
          </span>
          <button className={`auto-refresh ${autoRefresh ? 'is-active' : ''}`} type="button" aria-pressed={autoRefresh} onClick={() => setAutoRefresh((value) => !value)}>
            <span className="auto-refresh-dot" aria-hidden="true" />
            {autoRefresh ? 'Tự cập nhật · 1 phút' : 'Đã tắt tự cập nhật'}
          </button>
          <button className="btn btn-refresh" type="button" onClick={load} disabled={loading}>
            <Icon name="refresh" size={17} />
            <span>{loading ? 'Đang tải' : 'Làm mới'}</span>
          </button>
        </div>
      </header>

      {error && (
        <div className="alert error dashboard-error" role="alert">
          <span>{error}</span>
          <button className="text-button" type="button" onClick={load}>Thử lại</button>
        </div>
      )}

      {isLoadingInitial ? (
        <div className="dashboard-loading" role="status" aria-label="Đang tải dữ liệu tổng quan">
          <div className="loading-card" />
          <div className="loading-metrics"><div className="loading-card" /><div className="loading-card" /><div className="loading-card" /></div>
          <div className="loading-card loading-card--large" />
        </div>
      ) : (
        <>
          <section className={`risk-banner risk-banner--${areaStatus.level}`} aria-live="polite" aria-atomic="true">
            <div className="risk-banner-icon"><Icon name={areaStatus.level === 'unknown' ? 'pin' : areaStatus.level === 'clear' || areaStatus.level === 'low' ? 'shield' : 'warning'} size={23} /></div>
            <div className="risk-banner-content">
              <p className="risk-eyebrow">{areaStatus.eyebrow}</p>
              <h2>{areaStatus.title}</h2>
              <p>{areaStatus.description}</p>
            </div>
            <button className="risk-map-link" type="button" onClick={() => onNav?.('map')}>
              <span>Xem bản đồ</span><Icon name="arrow" size={16} />
            </button>
          </section>

          <section className="metric-grid" aria-label="Thống kê chính">
            <MetricCard label="Ổ dịch đã xác nhận" value={verifiedOutbreaks.length} detail="Toàn bộ thời gian" icon="outbreak" tone="green" />
            <MetricCard label="Đang hoạt động" value={activeOutbreaks.length} detail="Cần theo dõi" icon="warning" tone="red" />
            <MetricCard label="Trang trại trong vùng" value={exposure.affectedFarmIds.size} detail={`Trong ${exposure.trackedFarms.length} trang trại có tọa độ`} icon="farm" tone="orange" />
            <MetricCard label="Ca bệnh ghi nhận" value={reportedCases} detail="Từ ổ dịch đã xác nhận" icon="chart" tone="blue" />
            <MetricCard label="Thông báo" value={data.alerts.length} detail="Gửi đến tài khoản này" icon="bell" tone="violet" />
          </section>

          <section className="dashboard-panels">
            <article className="panel trend-panel">
              <div className="panel-heading">
                <div>
                  <h2>Diễn biến ổ dịch</h2>
                  <p>Số ổ dịch đã xác nhận theo tháng</p>
                </div>
                <span className="panel-period">6 tháng</span>
              </div>
              {verifiedOutbreaks.length === 0 ? (
                <div className="chart-empty"><Icon name="chart" size={25} /><span>Chưa có dữ liệu ổ dịch để hiển thị.</span></div>
              ) : <TrendChart months={monthlyTrend} />}
            </article>

            <article className="panel severity-panel">
              <div className="panel-heading">
                <div>
                  <h2>Mức độ ổ dịch</h2>
                  <p>Phân loại trên các ổ dịch đã xác nhận</p>
                </div>
                <span className="severity-total">{numberFormat.format(severityTotal)}</span>
              </div>
              <SeverityBreakdown outbreaks={verifiedOutbreaks} />
              <div className="panel-footnote">Đã khống chế hoặc đóng: <strong>{numberFormat.format(resolvedCount)}</strong></div>
            </article>
          </section>

          <section className="panel outbreaks-panel">
            <div className="panel-heading outbreaks-heading">
              <div>
                <h2>Lịch sử ổ dịch</h2>
                <p>{numberFormat.format(data.outbreaks.length)} bản ghi · hiển thị tối đa 6 ổ dịch gần đây</p>
              </div>
              <button className="link-button" type="button" onClick={() => onNav?.('outbreaks')}>
                Danh sách ổ dịch <Icon name="arrow" size={16} />
              </button>
            </div>

            <div className="filter-row" role="group" aria-label="Lọc lịch sử ổ dịch theo trạng thái">
              {statusFilters.map((filter) => (
                <button
                  className={`filter-chip ${statusFilter === filter.value ? 'active' : ''}`}
                  key={filter.value}
                  type="button"
                  aria-pressed={statusFilter === filter.value}
                  onClick={() => setStatusFilter(filter.value)}
                >
                  {filter.label}
                </button>
              ))}
            </div>

            {visibleOutbreaks.length === 0 ? (
              <div className="empty-state">
                <Icon name="outbreak" size={24} />
                <strong>Không có ổ dịch phù hợp</strong>
                <span>Thử chọn trạng thái khác hoặc kiểm tra lại sau.</span>
              </div>
            ) : (
              <div className="table-scroll">
                <table className="outbreak-table">
                  <thead>
                    <tr>
                      <th scope="col">Ổ dịch</th>
                      <th scope="col">Khu vực</th>
                      <th scope="col">Ngày ghi nhận</th>
                      <th scope="col">Ca bệnh</th>
                      <th scope="col">Mức độ</th>
                      <th scope="col">Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleOutbreaks.map((outbreak) => (
                      <tr key={outbreak.id}>
                        <td>
                          <span className="table-primary">{outbreak.virus_type}</span>
                          <span className="table-secondary">{outbreak.verified ? 'Đã xác nhận' : 'Chờ xác nhận'}</span>
                        </td>
                        <td>
                          <span className="area-cell"><Icon name="pin" size={14} />{[outbreak.hamlet, outbreak.commune, outbreak.district, outbreak.province].filter(Boolean).join(', ') || 'Chưa rõ'}</span>
                        </td>
                        <td>{formatDate(outbreak.reported_date)}</td>
                        <td className="number-cell">{numberFormat.format(Number(outbreak.cases_count) || 0)}</td>
                        <td><span className={`status-pill status-pill--${outbreak.severity}`}>{riskLabel[outbreak.severity] || outbreak.severity}</span></td>
                        <td><span className={`status-pill status-pill--state-${outbreak.status}`}>{outbreakStatusLabel[outbreak.status] || outbreak.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <p className="dashboard-disclaimer">
            <Icon name="shield" size={15} />
            Mức cảnh báo khu vực được đối chiếu với vị trí trang trại, bán kính ổ dịch và dữ liệu đã xác nhận. Đây là thông tin tham khảo; hãy liên hệ cán bộ thú y địa phương để được hướng dẫn.
          </p>
        </>
      )}
    </div>
  )
}
