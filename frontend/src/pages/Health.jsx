import { CheckCircle2, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../api/client'

const SERVICE_LABELS = {
  backend_api: 'Backend API',
  database: 'Database (MongoDB)',
  email_service: 'Email Service (Gmail SMTP)',
  groq_ai: 'Groq AI',
  authentication: 'Authentication (JWT + Argon2)',
}

const STATUS_CONFIG = {
  healthy:       { color: 'var(--success)', bg: 'var(--success-bg)', label: 'Healthy' },
  unavailable:   { color: 'var(--danger)',  bg: 'var(--danger-bg)',  label: 'Unavailable' },
  warning:       { color: 'var(--warning)', bg: 'var(--warning-bg)', label: 'Warning' },
  not_configured:{ color: 'var(--text-tertiary)', bg: 'var(--bg)',   label: 'Not configured' },
}

export default function Health() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.getHealth().then(setHealth)
    const id = setInterval(() => api.getHealth().then(setHealth), 15000)
    return () => clearInterval(id)
  }, [])

  if (!health) return (
    <Layout>
      <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Checking system status…</div>
      </div>
    </Layout>
  )

  const overall = STATUS_CONFIG[health.overall_status] ?? STATUS_CONFIG.warning

  return (
    <Layout>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h1 className="page-title" style={{ marginBottom: 4 }}>System Health</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            Live status — polled every 15 seconds. Never assumes healthy.
          </p>
        </div>
        <span className="badge" style={{ background: overall.bg, color: overall.color, borderColor: 'transparent', fontSize: 12 }}>
          Overall: {overall.label}
        </span>
      </div>

      <div className="card" style={{ overflow: 'hidden', maxWidth: 600 }}>
        {Object.entries(health.services).map(([key, status], i, arr) => {
          const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.warning
          const isOk = status === 'healthy'
          return (
            <div key={key} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '13px 18px',
              borderBottom: i < arr.length - 1 ? '1px solid var(--border)' : 'none',
            }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 500 }}>{SERVICE_LABELS[key] ?? key}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>{key}</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, color: cfg.color }}>
                {isOk
                  ? <CheckCircle2 size={15} />
                  : <XCircle size={15} />
                }
                <span style={{ fontSize: 12, fontWeight: 500 }}>{cfg.label}</span>
              </div>
            </div>
          )
        })}
      </div>
    </Layout>
  )
}
