import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Icon from '../components/Icon'
import userService from '../services/userService'

const emptyForm = { full_name: '', email: '', password: '', role: 'user' }
const roleNames = { admin: 'Quản trị viên', vet_officer: 'Cán bộ thú y', user: 'Người dùng' }

export default function Accounts({ user, onAccountUpdated }) {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [pageError, setPageError] = useState('')
  const [notice, setNotice] = useState('')
  const [query, setQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [dialog, setDialog] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)
  const [workingId, setWorkingId] = useState(null)
  const dialogRef = useRef(null)
  const previousFocus = useRef(null)
  const dialogLocked = useRef(false)
  dialogLocked.current = saving || Boolean(workingId)

  const load = useCallback(async () => {
    setLoading(true)
    setPageError('')
    try {
      setAccounts(await userService.all())
    } catch (err) {
      setPageError(err.message || 'Không thể tải danh sách tài khoản.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!dialog) return undefined
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKeyDown = (event) => {
      if (event.key === 'Escape' && !dialogLocked.current) {
        setDialog(null)
        return
      }
      if (event.key !== 'Tab' || !dialogRef.current) return
      const focusable = [...dialogRef.current.querySelectorAll(
        'button:not(:disabled), input:not(:disabled), select:not(:disabled), [href], [tabindex]:not([tabindex="-1"])',
      )].filter((element) => !element.hasAttribute('hidden'))
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
      if (previousFocus.current && document.contains(previousFocus.current)) previousFocus.current.focus()
    }
  }, [dialog])

  const activeCount = accounts.filter((account) => account.is_active).length
  const vetCount = accounts.filter((account) => account.role === 'vet_officer').length
  const inactiveCount = accounts.filter((account) => !account.is_active).length

  const visibleAccounts = useMemo(() => {
    const search = query.trim().toLocaleLowerCase('vi-VN')
    return accounts
      .filter((account) => roleFilter === 'all' || account.role === roleFilter)
      .filter((account) => statusFilter === 'all' || (statusFilter === 'active' ? account.is_active : !account.is_active))
      .filter((account) => !search || `${account.full_name} ${account.email}`.toLocaleLowerCase('vi-VN').includes(search))
      .sort((a, b) => a.full_name.localeCompare(b.full_name, 'vi'))
  }, [accounts, query, roleFilter, statusFilter])

  const openCreate = () => {
    previousFocus.current = document.activeElement
    setForm(emptyForm)
    setFormError('')
    setPageError('')
    setNotice('')
    setDialog({ mode: 'create' })
  }

  const openEdit = (account) => {
    previousFocus.current = document.activeElement
    setForm({ full_name: account.full_name, email: account.email, password: '', role: account.role })
    setFormError('')
    setPageError('')
    setNotice('')
    setDialog({ mode: 'edit', account })
  }

  const openConfirmation = (mode, account) => {
    previousFocus.current = document.activeElement
    setFormError('')
    setPageError('')
    setNotice('')
    setDialog({ mode, account })
  }

  const updateField = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!dialog || !['create', 'edit'].includes(dialog.mode)) return
    setSaving(true)
    setFormError('')
    setNotice('')
    const payload = {
      full_name: form.full_name.trim(),
      email: form.email.trim().toLowerCase(),
      role: form.role,
    }
    try {
      if (dialog.mode === 'create') {
        const created = await userService.create({ ...payload, password: form.password })
        setAccounts((list) => [created, ...list])
        setNotice(`Đã tạo tài khoản ${created.full_name}.`)
      } else {
        const updated = await userService.update(dialog.account.id, payload)
        setAccounts((list) => list.map((account) => account.id === updated.id ? updated : account))
        if (updated.id === user?.id) onAccountUpdated?.(updated)
        setNotice(`Đã cập nhật tài khoản ${updated.full_name}.`)
      }
      setDialog(null)
    } catch (err) {
      setFormError(err.message || 'Không thể lưu tài khoản. Vui lòng thử lại.')
    } finally {
      setSaving(false)
    }
  }

  const handleAccountStatus = async (account) => {
    setWorkingId(account.id)
    setPageError('')
    setNotice('')
    try {
      const updated = await userService.update(account.id, { is_active: !account.is_active })
      setAccounts((list) => list.map((item) => item.id === updated.id ? updated : item))
      setNotice(updated.is_active ? `Đã mở lại tài khoản ${updated.full_name}.` : `Đã vô hiệu hóa tài khoản ${updated.full_name}.`)
      setDialog(null)
    } catch (err) {
      const message = err.message || 'Không thể cập nhật trạng thái tài khoản.'
      if (dialog?.mode === 'deactivate') setFormError(message)
      else setPageError(message)
    } finally {
      setWorkingId(null)
    }
  }

  const handleDelete = async (account) => {
    setWorkingId(account.id)
    setPageError('')
    setNotice('')
    try {
      await userService.remove(account.id)
      setAccounts((list) => list.filter((item) => item.id !== account.id))
      setNotice(`Đã xóa tài khoản ${account.full_name}.`)
      setDialog(null)
    } catch (err) {
      setFormError(err.message || 'Không thể xóa tài khoản.')
    } finally {
      setWorkingId(null)
    }
  }

  const isOwnAccount = (account) => account.id === user?.id

  return (
    <div className="page accounts-page">
      <header className="accounts-header">
        <div>
          <p className="eyebrow">QUẢN TRỊ HỆ THỐNG</p>
          <h1>Quản lý tài khoản</h1>
          <p className="accounts-subtitle">Tạo người dùng, cấp quyền cán bộ thú y và quản lý quyền truy cập.</p>
        </div>
        <button className="btn account-create-btn" type="button" onClick={openCreate}>
          <Icon name="plus" size={18} /><span>Thêm tài khoản</span>
        </button>
      </header>

      {pageError && <div className="alert error" role="alert"><span>{pageError}</span><button className="text-button" type="button" onClick={load}>Tải lại</button></div>}
      {notice && <div className="alert success" role="status">{notice}</div>}

      <section className="account-stats" aria-label="Thống kê tài khoản">
        <div className="account-stat"><span className="account-stat-icon account-stat-icon--green"><Icon name="users" /></span><span className="account-stat-copy"><small>Tổng tài khoản</small><strong>{accounts.length}</strong></span></div>
        <div className="account-stat"><span className="account-stat-icon account-stat-icon--blue"><Icon name="shield" /></span><span className="account-stat-copy"><small>Đang hoạt động</small><strong>{activeCount}</strong></span></div>
        <div className="account-stat"><span className="account-stat-icon account-stat-icon--orange"><Icon name="farm" /></span><span className="account-stat-copy"><small>Cán bộ thú y</small><strong>{vetCount}</strong></span></div>
        <div className="account-stat"><span className="account-stat-icon account-stat-icon--violet"><Icon name="lock" /></span><span className="account-stat-copy"><small>Đã vô hiệu hóa</small><strong>{inactiveCount}</strong></span></div>
      </section>

      <section className="account-list-panel" aria-labelledby="account-list-title">
        <div className="account-list-heading">
          <div>
            <h2 id="account-list-title">Danh sách tài khoản</h2>
            <p>{loading ? 'Đang tải danh sách…' : `${visibleAccounts.length} tài khoản phù hợp`}</p>
          </div>
          <button className="btn account-refresh-btn" type="button" onClick={load} disabled={loading}>
            <Icon name="refresh" size={16} /><span>Làm mới</span>
          </button>
        </div>

        <div className="account-filters">
          <div className="account-search-wrap">
            <label htmlFor="account-search">Tìm tài khoản</label>
            <div className="account-search">
              <Icon name="search" size={17} />
              <input id="account-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nhập tên hoặc email" />
            </div>
          </div>
          <div className="account-filter-field">
            <label htmlFor="account-role-filter">Vai trò</label>
            <select id="account-role-filter" value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)}>
              <option value="all">Tất cả vai trò</option>
              <option value="admin">Quản trị viên</option>
              <option value="vet_officer">Cán bộ thú y</option>
              <option value="user">Người dùng</option>
            </select>
          </div>
          <div className="account-filter-field">
            <label htmlFor="account-status-filter">Trạng thái</label>
            <select id="account-status-filter" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="all">Tất cả trạng thái</option>
              <option value="active">Đang hoạt động</option>
              <option value="inactive">Đã vô hiệu hóa</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="accounts-loading" role="status" aria-label="Đang tải danh sách tài khoản">
            <span /><span /><span /><span />
          </div>
        ) : visibleAccounts.length === 0 ? (
          <div className="accounts-empty">
            <span className="account-empty-icon"><Icon name={query || roleFilter !== 'all' || statusFilter !== 'all' ? 'search' : 'users'} size={23} /></span>
            <strong>{pageError ? 'Không tải được danh sách' : accounts.length === 0 ? 'Chưa có tài khoản' : 'Không tìm thấy kết quả'}</strong>
            <p>{pageError ? 'Hãy kiểm tra kết nối rồi tải lại danh sách.' : accounts.length === 0 ? 'Tạo tài khoản đầu tiên cho người dùng hoặc cán bộ thú y.' : 'Thử thay đổi từ khóa hoặc bộ lọc.'}</p>
            {pageError && <button className="btn secondary" type="button" onClick={load}>Tải lại danh sách</button>}
            {!pageError && accounts.length === 0 && <button className="btn" type="button" onClick={openCreate}><Icon name="plus" size={16} />Tạo tài khoản</button>}
          </div>
        ) : (
          <div className="table-scroll account-table-scroll">
            <table className="account-table">
              <thead>
                <tr><th scope="col">Tài khoản</th><th scope="col">Vai trò</th><th scope="col">Trạng thái</th><th scope="col">Thao tác</th></tr>
              </thead>
              <tbody>
                {visibleAccounts.map((account) => (
                  <tr key={account.id}>
                    <td>
                      <div className="account-identity">
                        <span className={`account-avatar ${account.role === 'admin' ? 'account-avatar--admin' : account.role === 'vet_officer' ? 'account-avatar--vet' : ''}`} aria-hidden="true">
                          {account.full_name?.trim().charAt(0).toLocaleUpperCase('vi-VN') || 'T'}
                        </span>
                        <span className="account-identity-copy"><strong>{account.full_name}</strong><span>{account.email}</span></span>
                        {isOwnAccount(account) && <span className="account-you-badge">Bạn</span>}
                      </div>
                    </td>
                    <td><span className={`account-role account-role--${account.role}`}><span aria-hidden="true" />{roleNames[account.role] || account.role}</span></td>
                    <td><span className={`account-state ${account.is_active ? 'account-state--active' : 'account-state--inactive'}`}><span aria-hidden="true" />{account.is_active ? 'Hoạt động' : 'Đã khóa'}</span></td>
                    <td>
                      <div className="account-actions">
                        <button className="account-action" type="button" onClick={() => openEdit(account)} disabled={Boolean(workingId)} aria-label={`Sửa tài khoản ${account.full_name}`}>
                          <Icon name="edit" size={15} /><span>Sửa</span>
                        </button>
                        {!isOwnAccount(account) && (
                          <>
                            <button
                              className="account-action"
                              type="button"
                              disabled={Boolean(workingId)}
                              onClick={() => account.is_active ? openConfirmation('deactivate', account) : handleAccountStatus(account)}
                              aria-label={account.is_active ? `Vô hiệu hóa ${account.full_name}` : `Mở lại ${account.full_name}`}
                            >
                              <Icon name={account.is_active ? 'lock' : 'unlock'} size={15} /><span>{account.is_active ? 'Khóa' : 'Mở lại'}</span>
                            </button>
                            <button className="account-action account-action--danger" type="button" onClick={() => openConfirmation('delete', account)} disabled={Boolean(workingId)} aria-label={`Xóa tài khoản ${account.full_name}`}>
                              <Icon name="trash" size={15} /><span>Xóa</span>
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="accounts-note"><Icon name="shield" size={15} /> Tài khoản của bạn không thể tự khóa, xóa hoặc đổi vai trò. Tài khoản bị khóa có thể được mở lại sau này.</p>

      {dialog && (
        <div
          className="account-modal-backdrop"
          onMouseDown={(event) => { if (event.target === event.currentTarget && !saving && !workingId) setDialog(null) }}
        >
          <section className="account-modal" ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="account-dialog-title" aria-describedby="account-dialog-description">
            {['create', 'edit'].includes(dialog.mode) ? (
              <>
                <header className="account-modal-header">
                  <span className="account-modal-icon"><Icon name={dialog.mode === 'create' ? 'plus' : 'edit'} size={19} /></span>
                  <div>
                    <p className="eyebrow">QUẢN TRỊ TÀI KHOẢN</p>
                    <h2 id="account-dialog-title">{dialog.mode === 'create' ? 'Tạo tài khoản' : 'Sửa thông tin'}</h2>
                    <p id="account-dialog-description">{dialog.mode === 'create' ? 'Tạo tài khoản mới cho người dùng hoặc cán bộ thú y.' : `Cập nhật hồ sơ của ${dialog.account.full_name}.`}</p>
                  </div>
                  <button className="modal-close" type="button" onClick={() => setDialog(null)} disabled={saving} aria-label="Đóng cửa sổ">×</button>
                </header>
                <form className="account-form" onSubmit={handleSubmit}>
                  <div className="field">
                    <label htmlFor="account-full-name">Họ và tên</label>
                    <input id="account-full-name" autoFocus autoComplete="name" minLength={2} maxLength={255} value={form.full_name} onChange={updateField('full_name')} required />
                  </div>
                  <div className="field">
                    <label htmlFor="account-email">Email đăng nhập</label>
                    <input id="account-email" type="email" autoComplete="email" value={form.email} onChange={updateField('email')} required />
                  </div>
                  {dialog.mode === 'create' && (
                    <div className="field">
                      <label htmlFor="account-password">Mật khẩu khởi tạo</label>
                      <input id="account-password" type="password" autoComplete="new-password" minLength={8} maxLength={128} value={form.password} onChange={updateField('password')} aria-describedby="account-password-hint" required />
                      <small id="account-password-hint" className="field-hint">Ít nhất 8 ký tự. Người dùng có thể đổi mật khẩu sau khi đăng nhập.</small>
                    </div>
                  )}
                  <div className="field">
                    <label htmlFor="account-role">Vai trò</label>
                    <select id="account-role" value={form.role} onChange={updateField('role')} disabled={dialog.mode === 'edit' && isOwnAccount(dialog.account)}>
                      {form.role === 'admin' && <option value="admin">Quản trị viên</option>}
                      <option value="user">Người dùng</option>
                      <option value="vet_officer">Cán bộ thú y</option>
                    </select>
                    {dialog.mode === 'edit' && isOwnAccount(dialog.account) && <small className="field-hint">Bạn không thể tự đổi vai trò quản trị viên.</small>}
                  </div>
                  {formError && <div className="alert error" role="alert">{formError}</div>}
                  <footer className="account-modal-actions">
                    <button className="btn secondary" type="button" onClick={() => setDialog(null)} disabled={saving}>Hủy</button>
                    <button className="btn" type="submit" disabled={saving}>
                      {saving ? 'Đang lưu…' : dialog.mode === 'create' ? 'Tạo tài khoản' : 'Lưu thay đổi'}
                    </button>
                  </footer>
                </form>
              </>
            ) : (
              <>
                <header className="account-modal-header">
                  <span className={`account-modal-icon ${dialog.mode === 'delete' ? 'account-modal-icon--danger' : ''}`}><Icon name={dialog.mode === 'delete' ? 'trash' : 'lock'} size={19} /></span>
                  <div>
                    <p className="eyebrow">XÁC NHẬN THAO TÁC</p>
                    <h2 id="account-dialog-title">{dialog.mode === 'delete' ? 'Xóa tài khoản?' : 'Vô hiệu hóa tài khoản?'}</h2>
                    <p id="account-dialog-description">{dialog.mode === 'delete'
                      ? `Tài khoản ${dialog.account.full_name} sẽ bị xóa. Hồ sơ trang trại và ổ dịch vẫn được giữ lại nhưng sẽ bỏ liên kết với tài khoản này.`
                      : `${dialog.account.full_name} sẽ không thể đăng nhập cho đến khi quản trị viên mở lại tài khoản.`}</p>
                  </div>
                </header>
                {formError && <div className="alert error" role="alert">{formError}</div>}
                <footer className="account-modal-actions">
                  <button className="btn secondary" type="button" onClick={() => setDialog(null)} disabled={Boolean(workingId)} autoFocus>Hủy</button>
                  <button
                    className={`btn ${dialog.mode === 'delete' ? 'danger' : 'account-lock-confirm'}`}
                    type="button"
                    onClick={() => dialog.mode === 'delete' ? handleDelete(dialog.account) : handleAccountStatus(dialog.account)}
                    disabled={Boolean(workingId)}
                  >
                    {workingId ? 'Đang xử lý…' : dialog.mode === 'delete' ? 'Xóa tài khoản' : 'Vô hiệu hóa'}
                  </button>
                </footer>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
