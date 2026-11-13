import { useState } from 'react'
import authService from '../services/authService'

export default function Login({ onAuth }) {
  const [credentials, setCredentials] = useState({ username: '', password: '' })
  const [login, setLogin] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLogin(true)
    setError('')
    try {
      const user = await authService.login(credentials)
      onAuth(user)
    } catch (err) {
      setError(err.message || 'Không thể đăng nhập. Vui lòng thử lại.')
    } finally {
      setLogin(false)
    }
  }

  return (
    <div className="page">
      <h1>Đăng nhập</h1>
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
          <button className="btn" type="submit" disabled={login}>Đăng nhập</button>
        </form>
      </div>
      <p className="auth-switch"><a href="#register" onClick={(e) => { e.preventDefault(); onNavigate?.('register') }}>Chưa có tài khoản? Đăng ký</a></p>
    </div>
  )
}