import { useCallback, useEffect, useState } from 'react'
import './App.css'
import Navbar from './components/Navbar'
import Login from './components/Login'
import Register from './components/Register'
import Dashboard from './pages/Dashboard'
import Farms from './pages/Farms'
import Outbreaks from './pages/Outbreaks'
import Alerts from './pages/Alerts'

const validViews = new Set(['login', 'register', 'dashboard', 'farms', 'outbreaks', 'alerts'])
const getInitialView = () => {
  const hash = window.location.hash.replace(/^#\/?/, '')
  return validViews.has(hash) ? hash : 'login'
}

export default function App() {
  const [user, setUser] = useState(null)
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

  const logout = () => {
    localStorage.removeItem('access_token')
    setUser(null)
    go('login')
  }

  return (
    <div className="app">
      <Navbar user={user} currentView={view} onNavigate={go} onLogout={logout} />
      <main className="app-content">
        {view === 'login' && <Login onAuth={(u) => { setUser(u); go('dashboard') }} onNavigate={go} />}
        {view === 'register' && <Register onAuth={(u) => { setUser(u); go('dashboard') }} onNavigate={go} />}
        {view === 'dashboard' && <Dashboard onNav={go} />}
        {view === 'farms' && <Farms onNav={go} />}
        {view === 'outbreaks' && <Outbreaks onNav={go} />}
        {view === 'alerts' && <Alerts onNav={go} />}
      </main>
    </div>
  )
}
