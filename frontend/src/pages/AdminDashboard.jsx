import { useEffect, useState } from 'react'
import { Users, Activity, ShieldCheck, Gauge, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const STATUS_COLORS = {
  healthy: 'var(--success)',
  unavailable: 'var(--danger)',
  warning: 'var(--warning)',
  not_configured: 'var(--text-tertiary)',
}

export default function AdminDashboard() {
  const { user } = useAuth()
  const [memberCount, setMemberCount] = useState(null)
  const [health, setHealth] = useState(null)
  const isDev = user?.role === 'developer'

  useEffect(() => {
    api.listMembers().then(r => setMemberCount(r.total)).catch(() => {})
    api.getHealth().then(setHealth).catch(() => {})
  }, [])

  const overallColor = STATUS_COLORS[health?.overall_status] ?? STATUS_COLORS.warning

  return (
    <Layout>
      <div style={{ marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 4 }}>
          {isDev ? 'Developer Dashboard' : 'Team Admin Dashboard'}
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          {isDev
            ? 'Full access — cryptographic tools, system health, and member management.'
            : 'Manage your team members and monitor communication.'}
        </p>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12, marginBottom: 28 }}>
        <div className="card" style={{ padding: '16px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Members</span>
            <Users size={15} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          <div className="stat-value">{memberCount ?? '—'}</div>
          <div className="stat-label">active team members</div>
        </div>

        <div className="card" style={{ padding: '16px 18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>System</span>
            <Activity size={15} style={{ color: 'var(--text-tertiary)' }} />
          </div>
          <div className="stat-value" style={{ fontSize: 18, color: overallColor, textTransform: 'capitalize' }}>
            {health?.overall_status ?? '—'}
          </div>
          <div className="stat-label">overall status</div>
        </div>
      </div>

      {/* Quick nav */}
      <h2 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
        Quick Access
      </h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 480 }}>
        {[
          { to: '/admin/members', label: 'Manage team members', icon: Users },
          { to: '/admin/bulk-add', label: 'Bulk import members', icon: Users },
          ...(isDev ? [
            { to: '/simulation', label: 'Encryption demo', icon: ShieldCheck },
            { to: '/performance', label: 'Performance benchmarks', icon: Gauge },
            { to: '/health', label: 'System health', icon: Activity },
          ] : []),
        ].map(({ to, label, icon: Icon }) => (
          <Link key={to} to={to} style={{ textDecoration: 'none' }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 14px', borderRadius: 'var(--r-sm)',
              transition: 'background var(--t-fast)',
            }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <Icon size={15} style={{ color: 'var(--text-tertiary)', flexShrink: 0 }} />
              <span style={{ fontSize: 13, flex: 1 }}>{label}</span>
              <ArrowRight size={13} style={{ color: 'var(--text-tertiary)' }} />
            </div>
          </Link>
        ))}
      </div>
    </Layout>
  )
}
