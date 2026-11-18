import { useState } from 'react'
import authService from '../services/authService'

export default function Login({ onAuth, onNavigate }) {
  const [credentials, setCredentials] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const user = await authService.login(credentials)
      onAuth(user)
    } catch (err) {
      setError(err.message || 'Không thể đăng nhập. Vui lòng thử lại.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page auth-page">
      <h1>Đăng nhập</h1>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="login-email">Email</label>
            <input id="login-email" name="email" type="email" autoComplete="email" value={credentials.email} onChange={(e) => setCredentials({ ...credentials, email: e.target.value })} required />
          </div>
          <div className="field">
            <label htmlFor="login-password">Mật khẩu</label>
            <input id="login-password" name="password" type="password" autoComplete="current-password" value={credentials.password} onChange={(e) => setCredentials({ ...credentials, password: e.target.value })} required />
          </div>
          {error && <div className="alert error" role="alert">{error}</div>}
          <button className="btn" type="submit" disabled={loading}>Đăng nhập</button>
        </form>
      </div>
      <p className="auth-switch"><a href="#register" onClick={(e) => { e.preventDefault(); onNavigate?.('register') }}>Chưa có tài khoản? Đăng ký</a></p>
    </div>
  )
}
