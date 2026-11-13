import { useState } from 'react'
import authService from '../services/authService'

export default function Register({ onAuth }) {
  const [credentials, setCredentials] = useState({ username: '', password: '' })
  const [register, setRegister] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setRegister(true)
    setError('')
    try {
      const user = await authService.register(credentials)
      onAuth(user)
    } catch (err) {
      setError(err.message || 'Không thể đăng ký. Vui lòng thử lại.')
    } finally {
      setRegister(false)
    }
  }

  return (
    <div className="page">
      <h1>Đăng ký</h1>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Tên đăng nhập</label>
            <input value={credentials.username} onChange={(e) => setCredentials({ ...credentials, username: e.target.value })} required />
          </div>
          <div className="field">
            <label>Mật khẩu</label>
            <input type="password" value={credentials.password} onChange={(e) => setCredentials({ ...credentials, password: e.target.value })} required />
          </div>
          {error && <div className="alert error">{error}</div>}
          <button className="btn" type="submit" disabled={register}>Đăng ký</button>
        </form>
      </div>
      <p className="auth-switch"><a href="#login" onClick={(e) => { e.preventDefault(); onNavigate?.('login') }}>Đã có tài khoản? Đăng nhập</a></p>
    </div>
  )
}