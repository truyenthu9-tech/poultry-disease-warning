const links = [
  { path: 'login', label: 'Đăng nhập', public: true },
  { path: 'register', label: 'Đăng ký', public: true },
  { path: 'dashboard', label: 'Tổng quan' },
  { path: 'farms', label: 'Trang trại' },
  { path: 'outbreaks', label: 'Bùng phát' },
  { path: 'alerts', label: 'Thông báo' },
]

export default function Navbar({ user, currentView, onNavigate, onLogout }) {
  return (
    <nav className="navbar">
      <button className="brand" type="button" onClick={() => onNavigate('dashboard')}>Poultry Disease Warning</button>
      <div className="links">
        {links.filter((link) => link.public || user).map((link) => (
          <a
            key={link.path}
            href={`#${link.path}`}
            className={currentView === link.path ? 'active' : ''}
            onClick={(event) => { event.preventDefault(); onNavigate(link.path) }}
          >
            {link.label}
          </a>
        ))}
        {user && <button type="button" onClick={onLogout}>Đăng xuất</button>}
      </div>
    </nav>
  )
}
