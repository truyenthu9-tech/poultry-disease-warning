import { useEffect, useState } from 'react'
import MapView, { MapLegend } from '../components/MapView'
import farmService from '../services/farmService'
import outbreakService from '../services/outbreakService'

export default function MapPage() {
  const [data, setData] = useState({ farms: [], outbreaks: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showFarms, setShowFarms] = useState(true)
  const [showOutbreaks, setShowOutbreaks] = useState(true)

  useEffect(() => {
    Promise.all([farmService.all(), outbreakService.all()])
      .then(([farms, outbreaks]) => setData({ farms, outbreaks }))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <h1>Bản đồ</h1>
      {loading && <p className="loading-message">Đang tải bản đồ…</p>}
      {error && <div className="alert error" role="alert">{error}</div>}
      {!loading && !error && (
        <>
          <p className="map-toolbar">
            <label><input type="checkbox" checked={showFarms} onChange={(e) => setShowFarms(e.target.checked)} /> Trang trại ({data.farms.length})</label>
            <label><input type="checkbox" checked={showOutbreaks} onChange={(e) => setShowOutbreaks(e.target.checked)} /> Ổ dịch ({data.outbreaks.length})</label>
          </p>
          <MapLegend />
          <MapView
            height="calc(100vh - 230px)"
            farms={showFarms ? data.farms : []}
            outbreaks={showOutbreaks ? data.outbreaks : []}
          />
        </>
      )}
    </div>
  )
}
