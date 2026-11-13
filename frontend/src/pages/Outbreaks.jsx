import { useEffect, useState } from 'react'
import outbreakService from '../services/outbreakService'

export default function Outbreaks({ onNav }) {
  const [outbreaks, setOutbreaks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    outbreakService.all()
      .then(setOutbreaks)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <h1>Bùng phát bệnh</h1>
      {loading && <p>Loading...</p>}
      {!loading && outbreaks.length === 0 && <p>Chưa có bùng phát nào.</p>}
      <table>
        <thead>
          <tr><th>ID</th><th>Tên</th><th>Tỉnh</th><th>Mức độ</th><th>Trạng thái</th></tr>
        </thead>
        <tbody>
          {outbreaks.map((outbreak) => (
            <tr key={outbreak.id}>
              <td>{outbreak.id}</td>
              <td>{outbreak.name}</td>
              <td>{outbreak.province}</td>
              <td>{outbreak.severity}</td>
              <td>{outbreak.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}