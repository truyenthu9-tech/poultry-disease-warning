import Icon from './Icon'

const links = [
  { path: 'dashboard', label: 'Tổng quan', icon: 'overview' },
  { path: 'farms', label: 'Trang trại', icon: 'farm' },
  { path: 'farm-requests', label: 'Đăng ký trại', icon: 'farm' },
  { path: 'outbreak-reports', label: 'Báo cáo dịch', icon: 'outbreak' },
  { path: 'outbreaks', label: 'Ổ dịch', icon: 'outbreak' },
  { path: 'map', label: 'Bản đồ', icon: 'map' },
  { path: 'alerts', label: 'Thông báo', icon: 'bell' },
]

const publicLinks = [
  { path: 'login', label: 'Đăng nhập' },
  { path: 'register', label: 'Đăng ký' },
]

const roleLabel = {
  admin: 'Quản trị viên',
  vet_officer: 'Cán bộ thú y',
  farm_owner: 'Chủ trang trại',
  user: 'Người dùng',
}

export default function Navbar({ user, currentView, onNavigate, onLogout }) {
  const canReviewFarms = ['admin', 'vet_officer'].includes(user?.role)
  const signedInLinks = links.map((link) => {
    if (link.path === 'farm-requests') return { ...link, label: canReviewFarms ? 'Duyệt hồ sơ trại' : 'Đăng ký trại' }
    if (link.path === 'outbreak-reports') return { ...link, label: canReviewFarms ? 'Duyệt báo cáo dịch' : 'Báo cáo dịch' }
    return link
  })
  const navItems = user
    ? (user.role === 'admin'
      ? [{ path: 'accounts', label: 'Tài khoản', icon: 'users' }, ...signedInLinks]
      : signedInLinks)
    : publicLinks
  const name = user?.full_name || user?.email || 'Tài khoản'
  const initial = name.trim().charAt(0).toLocaleUpperCase('vi-VN') || 'T'

  return (
    <nav className={`navbar ${user ? 'navbar--signed-in' : 'navbar--public'}`} aria-label="Điều hướng chính">
      <div className="navbar-top">
        <button
          className="brand"
          type="button"
          aria-label={user ? (user.role === 'admin' ? 'Về quản lý tài khoản' : 'Về trang tổng quan') : 'Về trang đăng nhập'}
          onClick={() => onNavigate(user ? (user.role === 'admin' ? 'accounts' : 'dashboard') : 'login')}
        >
          <span className="brand-mark"><Icon name="bird" size={22} /></span>
          <span className="brand-copy">
            <strong>Poultry Disease Warning</strong>
            <small>GIÁM SÁT DỊCH BỆNH</small>
          </span>
        </button>

        {user && (
          <div className="profile-card">
            <span className="profile-avatar" aria-hidden="true">{initial}</span>
            <span className="profile-copy">
              <strong title={name}>{name}</strong>
              <small>{roleLabel[user.role] || 'Tài khoản'}</small>
            </span>
            <button className="logout-btn" type="button" onClick={onLogout} aria-label="Đăng xuất">
              <span>Đăng xuất</span><Icon name="arrow" size={16} />
            </button>
          </div>
        )}
      </div>

      <div className="nav-section-label">{user ? 'Không gian làm việc' : 'Tài khoản'}</div>
      <div className="links">
        {navItems.map((link) => (
          <a
            key={link.path}
            href={`#${link.path}`}
            className={currentView === link.path ? 'active' : ''}
            aria-current={currentView === link.path ? 'page' : undefined}
            onClick={(event) => { event.preventDefault(); onNavigate(link.path) }}
          >
            {link.icon && <Icon name={link.icon} size={18} />}
            <span>{link.label}</span>
          </a>
        ))}
      </div>

      {user && (
        <div className="nav-footnote">
          <Icon name="shield" size={17} />
          <span>Dữ liệu ổ dịch đã xác nhận được dùng để tính cảnh báo khu vực.</span>
        </div>
      )}
    </nav>
  )
}
