import { useState } from 'react'
import authService from '../services/authService'

export default function Register({ onAuth, onNavigate }) {
  const [form, setForm] = useState({ full_name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const user = await authService.register(form)
      onAuth(user)
    } catch (err) {
      setError(typeof err.message === 'string' ? err.message : 'Không thể đăng ký. Vui lòng thử lại.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page auth-page">
      <h1>Đăng ký</h1>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="register-name">Họ và tên</label>
            <input id="register-name" name="name" autoComplete="name" value={form.full_name} minLength={2} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
          </div>
          <div className="field">
            <label htmlFor="register-email">Email</label>
            <input id="register-email" name="email" type="email" autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          <div className="field">
            <label htmlFor="register-password">Mật khẩu (tối thiểu 8 ký tự)</label>
            <input id="register-password" name="new-password" type="password" autoComplete="new-password" value={form.password} minLength={8} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </div>
          {error && <div className="alert error" role="alert">{error}</div>}
          <button className="btn" type="submit" disabled={loading}>Đăng ký</button>
        </form>
      </div>
      <p className="auth-switch"><a href="#login" onClick={(e) => { e.preventDefault(); onNavigate?.('login') }}>Đã có tài khoản? Đăng nhập</a></p>
    </div>
  )
}
