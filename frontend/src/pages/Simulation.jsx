import { useState } from 'react'
import { Play, ShieldCheck, ArrowDown, AlertCircle } from 'lucide-react'
import Layout from '../components/Layout'
import { api } from '../api/client'

const STAGE_COLORS = {
  'ML-KEM-768 Key Generation': '#4f46e5',
  'ML-KEM-768 Encapsulation':  '#7c3aed',
  'ML-KEM-768 Decapsulation':  '#6d28d9',
  'HKDF-SHA256 Key Derivation':'#0369a1',
  'AES-256-GCM Encryption':    '#15803d',
  'AES-256-GCM Decryption':    '#b45309',
}

export default function Simulation() {
  const [message, setMessage] = useState('send me the report by 5pm tomorrow')
  const [result, setResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  const run = async () => {
    setError(''); setRunning(true); setResult(null)
    try {
      const res = await api.runSimulation(message)
      setResult(res)
    } catch (e) { setError(e.message) }
    finally { setRunning(false) }
  }

  return (
    <Layout>
      <h1 className="page-title" style={{ marginBottom: 4 }}>Encryption Demo</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 22, maxWidth: 580 }}>
        Runs the real ML-KEM-768 → HKDF-SHA256 → AES-256-GCM pipeline on any message.
        No private keys or passwords are shown — only metadata, sizes, and timings.
      </p>

      <div className="card" style={{ padding: 16, marginBottom: 20, maxWidth: 580 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            className="input"
            value={message}
            onChange={e => setMessage(e.target.value)}
            placeholder="Sample message to encrypt…"
          />
          <button className="btn btn-primary" onClick={run} disabled={running || !message.trim()}>
            <Play size={14} /> {running ? 'Running…' : 'Run'}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 14, maxWidth: 580 }}><AlertCircle size={14} />{error}</div>}

      {result && (
        <div className="fade-in" style={{ maxWidth: 580 }}>
          {/* Result header */}
          <div className="card" style={{ padding: '12px 16px', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 10 }}>
            <ShieldCheck size={17} style={{ color: result.success ? 'var(--success)' : 'var(--danger)', flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>
                {result.success ? 'Message recovered and authenticated.' : 'Simulation failed.'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                All operations completed on the real cryptographic library — no mocked output.
              </div>
            </div>
          </div>

          {/* Stages */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {result.stages.map((stage, i) => {
              const accent = STAGE_COLORS[stage.stage] ?? 'var(--accent)'
              const entries = Object.entries(stage).filter(([k]) => !['stage', 'duration_ms'].includes(k))
              return (
                <div key={i}>
                  <div className="card" style={{ padding: '12px 16px', borderLeft: `3px solid ${accent}` }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: entries.length ? 8 : 0 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{stage.stage}</span>
                      {stage.duration_ms !== undefined && (
                        <span className="badge badge-neutral">{stage.duration_ms} ms</span>
                      )}
                    </div>
                    {entries.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 16px' }}>
                        {entries.map(([k, v]) => (
                          <div key={k} style={{ fontSize: 12 }}>
                            <span style={{ color: 'var(--text-tertiary)' }}>{k}: </span>
                            <span className="mono" style={{ color: 'var(--text-primary)' }}>{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {i < result.stages.length - 1 && (
                    <div style={{ display: 'flex', justifyContent: 'center', padding: '2px 0' }}>
                      <ArrowDown size={13} style={{ color: 'var(--text-tertiary)' }} />
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </Layout>
  )
}
