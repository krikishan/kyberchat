import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { useState } from 'react'
import { api } from '../api/client'
import { CheckCircle2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { setToken } from '../api/client'

const ROLE_LABELS = { developer: 'Developer', admin: 'Team Admin', user: 'Team Member' }

export default function Profile() {
  const { user } = useAuth()
  if (!user) return null

  const rows = [
    { label: 'Name',     value: user.name },
    { label: 'Username', value: `@${user.username}` },
    { label: 'Email',    value: user.email },
    { label: 'Role',     value: ROLE_LABELS[user.role] ?? user.role },
  ]

  return (
    <Layout>
      <h1 className="page-title" style={{ marginBottom: 20 }}>Your Account</h1>
      <div style={{ maxWidth: 480 }}>
        <div className="card" style={{ overflow: 'hidden' }}>
          {/* Avatar header */}
          <div style={{ padding: '20px 20px 16px', display: 'flex', alignItems: 'center', gap: 14, borderBottom: '1px solid var(--border)' }}>
            <div style={{
              width: 48, height: 48, borderRadius: '50%',
              background: 'var(--accent-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 20, fontWeight: 700, color: 'var(--accent)',
            }}>
              {user.name?.[0]?.toUpperCase() ?? '?'}
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>{user.name}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>@{user.username}</div>
            </div>
            <span className="badge badge-accent" style={{ marginLeft: 'auto' }}>{ROLE_LABELS[user.role] ?? user.role}</span>
          </div>
          {/* Details */}
          {rows.map(({ label, value }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '11px 20px', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{label}</span>
              <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  )
}
