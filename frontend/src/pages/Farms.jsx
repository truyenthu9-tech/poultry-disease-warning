import { useEffect, useState } from 'react'
import farmService from '../services/farmService'

export default function Farms({ onNav }) {
  const [farms, setFarms] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    farmService.all()
      .then(setFarms)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <h1>Quản lý trang trại</h1>
      {loading && <p>Loading...</p>}
      {!loading && farms.length === 0 && <p>Chưa có trang trại nào.</p>}
      <table>
        <thead>
          <tr><th>ID</th><th>Tên</th><th>Địa chỉ</th><th>Tỉnh</th><th>Điện thoại</th><th>Trạng thái</th></tr>
        </thead>
        <tbody>
          {farms.map((farm) => (
            <tr key={farm.id}>
              <td>{farm.id}</td>
              <td>{farm.name}</td>
              <td>{farm.address}</td>
              <td>{farm.province}</td>
              <td>{farm.phone}</td>
              <td>{farm.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}