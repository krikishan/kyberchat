import { MessageSquare, UsersRound, FileText, Sparkles, Shield } from 'lucide-react'
import { Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'

const cards = [
  { to: '/chats',   label: 'Individual Chats',   icon: MessageSquare, desc: 'Message team members directly, end-to-end encrypted.' },
  { to: '/groups',  label: 'Group Chats',         icon: UsersRound,    desc: 'Collaborate in shared groups with key-per-member encryption.' },
  { to: '/files',   label: 'Files',               icon: FileText,      desc: 'Browse and download shared attachments.' },
  { to: '/ai',      label: 'AI Message Enhancer', icon: Sparkles,      desc: 'Polish a draft before sending — you always approve the final text.' },
]

export default function Home() {
  const { user } = useAuth()
  return (
    <Layout>
      <div style={{ marginBottom: 28 }}>
        <h1 className="page-title" style={{ marginBottom: 4 }}>
          Welcome back{user?.name ? `, ${user.name.split(' ')[0]}` : ''}.
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 5 }}>
          <Shield size={13} />
          Messages protected with ML-KEM-768 · HKDF-SHA256 · AES-256-GCM
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
        {cards.map(({ to, label, icon: Icon, desc }) => (
          <Link
            key={to} to={to}
            style={{ textDecoration: 'none' }}
          >
            <div className="card fade-in" style={{
              padding: '18px 18px 16px',
              transition: 'box-shadow var(--t-base), border-color var(--t-base)',
              cursor: 'pointer',
            }}
              onMouseEnter={e => { e.currentTarget.style.boxShadow = 'var(--shadow-md)'; e.currentTarget.style.borderColor = 'var(--border-strong)' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = ''; e.currentTarget.style.borderColor = '' }}
            >
              <div style={{
                width: 34, height: 34, borderRadius: 8,
                background: 'var(--accent-subtle)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: 12,
              }}>
                <Icon size={16} color="var(--accent)" />
              </div>
              <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 4, color: 'var(--text-primary)' }}>{label}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{desc}</div>
            </div>
          </Link>
        ))}
      </div>
    </Layout>
  )
}
