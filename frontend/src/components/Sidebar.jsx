import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, MessageSquare, UsersRound, FileText,
  Users, UserPlus, ShieldCheck, Activity, Gauge, Sparkles,
  User, LogOut, KeyRound, X, Layers,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import Logo from './Logo'

/* Navigation structure by role */
function getNavSections(role) {
  const commsLinks = [
    { to: '/chats', label: 'Chats', icon: MessageSquare },
    { to: '/groups', label: 'Group Chats', icon: UsersRound },
    { to: '/members', label: 'Team', icon: Users },
    { to: '/files', label: 'Files', icon: FileText },
  ]

  if (role === 'developer') {
    return [
      {
        title: 'Overview',
        links: [{ to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true }],
      },
      {
        title: 'Organization',
        links: [
          { to: '/admin/teams', label: 'Teams & Leads', icon: Layers },
          { to: '/admin/members', label: 'All Members', icon: Users },
          { to: '/admin/bulk-add', label: 'Bulk Import', icon: UserPlus },
        ],
      },
      {
        title: 'Communication',
        links: commsLinks,
      },
      {
        title: 'Developer Tools',
        links: [
          { to: '/simulation', label: 'Encryption Demo', icon: ShieldCheck },
          { to: '/performance', label: 'Performance', icon: Gauge },
          { to: '/health', label: 'System Health', icon: Activity },
        ],
      },
    ]
  }

  if (role === 'admin') {
    return [
      {
        title: 'Overview',
        links: [{ to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true }],
      },
      {
        title: 'Organization',
        links: [
          { to: '/admin/teams', label: 'My Team', icon: Layers },
          { to: '/admin/members', label: 'Team Members', icon: Users },
          { to: '/admin/bulk-add', label: 'Bulk Import', icon: UserPlus },
        ],
      },
      {
        title: 'Communication',
        links: commsLinks,
      },
    ]
  }

  // user
  return [
    {
      title: 'Home',
      links: [{ to: '/', label: 'Home', icon: LayoutDashboard, end: true }],
    },
    {
      title: 'Communication',
      links: [
        ...commsLinks,
        { to: '/ai', label: 'AI Enhancer', icon: Sparkles },
      ],
    },
  ]
}

const ROLE_LABELS = { developer: 'Developer', admin: 'Team Admin', user: 'Member' }

export default function Sidebar({ mobileOpen = false, onClose }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const sections = getNavSections(user?.role)

  const handleLogout = async () => {
    onClose?.()
    await logout()
    navigate('/login')
  }

  const handleNavClick = () => {
    onClose?.()
  }

  return (
    <>
      {mobileOpen && (
        <div
          className="mobile-backdrop"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside className={`app-sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
        {/* Brand */}
        <div style={{
          padding: '18px 16px 14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border)',
        }}>
          <Logo size={28} subtitle={ROLE_LABELS[user?.role] ?? 'Secure Comms'} />
          <button
            type="button"
            className="btn btn-ghost btn-icon btn-sm mobile-close-btn"
            onClick={onClose}
            aria-label="Close navigation"
          >
            <X size={16} />
          </button>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '10px 8px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {sections.map((section) => (
            <div key={section.title}>
              <div className="nav-section-label">{section.title}</div>
              {section.links.map(({ to, label, icon: Icon, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  onClick={handleNavClick}
                  className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                >
                  <Icon className="nav-item-icon" />
                  {label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div style={{ padding: '8px 8px 12px', borderTop: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 2 }}>
          <NavLink to="/profile" onClick={handleNavClick} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            <User className="nav-item-icon" />
            {user?.name}
          </NavLink>
          <NavLink to="/change-password" onClick={handleNavClick} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            <KeyRound className="nav-item-icon" />
            Change Password
          </NavLink>
          <button className="nav-item" onClick={handleLogout} style={{ color: 'var(--danger)' }}>
            <LogOut className="nav-item-icon" style={{ color: 'var(--danger)' }} />
            Sign out
          </button>
        </div>
      </aside>
    </>
  )
}
