import { useEffect } from 'react'
import { Circle, CircleMarker, MapContainer, Popup, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { outbreakStatusLabel, poultryLabel, riskColor, riskLabel } from '../utils/labels'

const HANOI = [21.03, 105.85]

const hasLocation = (item) => item?.location
  && Number.isFinite(item.location.latitude)
  && Number.isFinite(item.location.longitude)
const toLatLng = (item) => [item.location.latitude, item.location.longitude]

// Tự co bản đồ cho vừa mọi điểm đang hiển thị
function FitBounds({ points }) {
  const map = useMap()
  useEffect(() => {
    if (points.length === 0) return
    if (points.length === 1) { map.setView(points[0], 12); return }
    map.fitBounds(points, { padding: [40, 40], maxZoom: 13 })
  }, [map, points])
  return null
}

function FocusAdministrativeArea({ focus }) {
  const map = useMap()
  useEffect(() => {
    if (focus?.center && Number.isFinite(focus.zoom)) {
      map.flyTo(focus.center, focus.zoom, { duration: 1.1 })
    }
  }, [focus?.key, focus?.center, focus?.zoom, map])
  return null
}

// Cho phép bấm lên bản đồ để chọn tọa độ
function ClickToPick({ onPick }) {
  useMapEvents({
    click: (e) => onPick({ latitude: Number(e.latlng.lat.toFixed(6)), longitude: Number(e.latlng.lng.toFixed(6)) }),
  })
  return null
}

/**
 * Bản đồ trang trại và ổ dịch.
 * farms, outbreaks: danh sách lấy từ API, mỗi phần tử có location {latitude, longitude}
 * picked: điểm đang chọn {latitude, longitude}, onPick: hàm gọi khi bấm lên bản đồ
 */
export default function MapView({ farms = [], outbreaks = [], height = 480, picked, onPick, focus }) {
  const farmList = farms.filter(hasLocation)
  const outbreakList = outbreaks.filter(hasLocation)
  const pickedPoint = picked && Number.isFinite(picked.latitude) && Number.isFinite(picked.longitude)
    ? [picked.latitude, picked.longitude]
    : null

  const points = [...farmList.map(toLatLng), ...outbreakList.map(toLatLng)]

  return (
    <div className="map-wrap" style={{ height }}>
      <MapContainer center={HANOI} zoom={10} zoomSnap={0.5} scrollWheelZoom style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {!pickedPoint && !focus?.center && <FitBounds points={points} />}
        <FocusAdministrativeArea focus={focus} />
        {onPick && <ClickToPick onPick={onPick} />}

        {outbreakList.map((o) => {
          const color = riskColor[o.severity] || '#dc2626'
          const active = o.status === 'active'
          return (
            <span key={o.id}>
              {o.radius_km > 0 && (
                <Circle
                  center={toLatLng(o)}
                  radius={o.radius_km * 1000}
                  pathOptions={{ color, weight: 1, fillColor: color, fillOpacity: active ? 0.15 : 0.05, dashArray: active ? undefined : '6 6' }}
                />
              )}
              <CircleMarker center={toLatLng(o)} radius={9} pathOptions={{ color: '#fff', weight: 2, fillColor: color, fillOpacity: 1 }}>
                <Popup>
                  <strong>Ổ dịch {o.virus_type}</strong><br />
                  {[o.hamlet, o.commune, o.district, o.province].filter(Boolean).join(', ')}<br />
                  Số ca: {o.cases_count}<br />
                  Mức độ: {riskLabel[o.severity] || o.severity}<br />
                  Trạng thái: {outbreakStatusLabel[o.status] || o.status}<br />
                  Bán kính cảnh báo: {o.radius_km} km
                </Popup>
              </CircleMarker>
            </span>
          )
        })}

        {farmList.map((f) => (
          <CircleMarker key={f.id} center={toLatLng(f)} radius={7} pathOptions={{ color: '#fff', weight: 2, fillColor: '#2563eb', fillOpacity: 1 }}>
            <Popup>
              <strong>{f.name}</strong><br />
              {f.owner_name ? <>Chủ trại: {f.owner_name}<br /></> : null}
              {poultryLabel[f.poultry_type] || f.poultry_type}, {f.capacity} con<br />
              {[f.hamlet, f.commune, f.district, f.province].filter(Boolean).join(', ')}<br />
              {f.phone ? <>ĐT: {f.phone}</> : null}{f.email ? <><br />Email: {f.email}</> : null}
            </Popup>
          </CircleMarker>
        ))}

        {pickedPoint && (
          <CircleMarker center={pickedPoint} radius={10} pathOptions={{ color: '#111827', weight: 3, fillColor: '#facc15', fillOpacity: 1 }}>
            <Popup>Vị trí đã chọn<br />{pickedPoint[0]}, {pickedPoint[1]}</Popup>
          </CircleMarker>
        )}
      </MapContainer>
    </div>
  )
}

export function MapLegend() {
  return (
    <p className="map-legend">
      <span className="dot" style={{ background: '#2563eb' }} /> Trang trại
      <span className="dot" style={{ background: '#dc2626' }} /> Ổ dịch, vòng tròn là bán kính cảnh báo
      <span className="dot dashed" /> Ổ dịch đã khống chế hoặc đã đóng
    </p>
  )
}
