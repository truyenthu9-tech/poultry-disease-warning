import { useCallback, useEffect, useState } from 'react'
import './App.css'
import Navbar from './components/Navbar'
import Login from './components/Login'
import Register from './components/Register'
import Dashboard from './pages/Dashboard'
import Farms from './pages/Farms'
import Outbreaks from './pages/Outbreaks'
import Alerts from './pages/Alerts'
import MapPage from './pages/MapPage'
import Accounts from './pages/Accounts'
import FarmRegistrations from './pages/FarmRegistrations'
import OutbreakReports from './pages/OutbreakReports'
import authService from './services/authService'

const validViews = new Set(['login', 'register', 'dashboard', 'farms', 'farm-requests', 'outbreaks', 'outbreak-reports', 'alerts', 'map', 'accounts'])
const publicViews = new Set(['login', 'register'])
const getInitialView = () => {
  const hash = window.location.hash.replace(/^#\/?/, '')
  return validViews.has(hash) ? hash : 'login'
}

export default function App() {
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(() => Boolean(localStorage.getItem('access_token')))
  const [view, setView] = useState(getInitialView)

  const go = useCallback((path) => {
    if (!validViews.has(path)) return
    setView(path)
    if (window.location.hash !== `#${path}`) window.location.hash = path
  }, [])

  useEffect(() => {
    const onHashChange = () => setView(getInitialView())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  // Token hết hạn: apiClient xóa token và phát sự kiện này
  useEffect(() => {
    const onUnauthorized = () => { setUser(null); go('login') }
    window.addEventListener('auth:unauthorized', onUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', onUnauthorized)
  }, [go])

  // Khôi phục phiên đăng nhập khi tải lại trang
  useEffect(() => {
    if (!localStorage.getItem('access_token')) return
    authService.current()
      .then((currentUser) => {
        setUser(currentUser)
        if (publicViews.has(getInitialView())) {
          go(currentUser.role === 'admin' ? 'accounts' : 'dashboard')
        }
      })
      .catch(() => localStorage.removeItem('access_token'))
      .finally(() => setChecking(false))
  }, [go])

  const logout = () => {
    authService.logout()
    setUser(null)
    go('login')
  }

  // Chỉ quản trị viên và cán bộ thú y được thêm, sửa, xóa và tạo cảnh báo
  const canWrite = Boolean(user && ['admin', 'vet_officer'].includes(user.role))
  const isAdmin = user?.role === 'admin'

  const onAuth = (u) => { setUser(u); go(u?.role === 'admin' ? 'accounts' : 'dashboard') }

  if (checking) return <div className="app app--loading"><main className="app-content"><p className="loading-message">Đang khôi phục phiên đăng nhập…</p></main></div>

  // Chưa đăng nhập: chỉ được vào đăng nhập/đăng ký. Đã đăng nhập: không còn vào lại hai trang này.
  const activeView = user
    ? (publicViews.has(view) ? (isAdmin ? 'accounts' : 'dashboard') : (view === 'accounts' && !isAdmin ? 'dashboard' : view))
    : (publicViews.has(view) ? view : 'login')

  return (
    <div className={`app ${user ? 'app--authenticated' : 'app--public'}`}>
      <a className="skip-link" href="#main-content">Bỏ qua đến nội dung</a>
      <Navbar user={user} currentView={activeView} onNavigate={go} onLogout={logout} />
      <main className="app-content" id="main-content" tabIndex="-1">
        {activeView === 'login' && <Login onAuth={onAuth} onNavigate={go} />}
        {activeView === 'register' && <Register onAuth={onAuth} onNavigate={go} />}
        {activeView === 'dashboard' && <Dashboard onNav={go} user={user} />}
        {activeView === 'farms' && <Farms onNav={go} canWrite={canWrite} />}
        {activeView === 'farm-requests' && <FarmRegistrations user={user} canReview={canWrite} onNav={go} />}
        {activeView === 'outbreak-reports' && <OutbreakReports user={user} canReview={canWrite} />}
        {activeView === 'outbreaks' && <Outbreaks onNav={go} canWrite={canWrite} />}
        {activeView === 'map' && <MapPage />}
        {activeView === 'alerts' && <Alerts onNav={go} canWrite={canWrite} />}
        {activeView === 'accounts' && isAdmin && <Accounts user={user} onAccountUpdated={setUser} />}
      </main>
    </div>
  )
}
