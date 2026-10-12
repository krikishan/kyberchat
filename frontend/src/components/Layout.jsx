import { useState } from 'react'
import { Menu, ShieldCheck } from 'lucide-react'
import Sidebar from './Sidebar'
import { useAuth } from '../context/AuthContext'

export function MobileHeader({ onOpenMenu }) {
  const { user } = useAuth()
  return (
    <header className="mobile-header">
      <button 
        type="button" 
        className="btn btn-ghost btn-icon btn-sm" 
        onClick={onOpenMenu}
        aria-label="Open Navigation Menu"
      >
        <Menu size={18} />
      </button>
      <div className="mobile-brand">
        <div className="mobile-brand-icon">
          <ShieldCheck size={14} color="#fff" />
        </div>
        <span className="mobile-brand-text">KyberChat</span>
      </div>
      <div className="mobile-user-badge" title={user?.name || user?.username}>
        {(user?.name || user?.username || 'U')[0].toUpperCase()}
      </div>
    </header>
  )
}

export default function Layout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="app-shell">
      <MobileHeader onOpenMenu={() => setMobileOpen(true)} />
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}

export function FullLayout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="app-shell">
      <MobileHeader onOpenMenu={() => setMobileOpen(true)} />
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      <div className="main-content-full">
        {children}
      </div>
    </div>
  )
}
