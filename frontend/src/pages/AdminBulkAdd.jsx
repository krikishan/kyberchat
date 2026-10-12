import { useState } from 'react'
import { ClipboardList, Check, ArrowLeft, AlertCircle, CheckCircle2, UserPlus } from 'lucide-react'
import Layout from '../components/Layout'
import { api } from '../api/client'

const STEPS = ['Paste', 'Review', 'Done']

export default function AdminBulkAdd() {
  const [step, setStep] = useState(0)
  const [rawText, setRawText] = useState('')
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handlePreview = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const res = await api.bulkPreview(rawText)
      setPreview(res); setStep(1)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  const handleConfirm = async () => {
    setError(''); setLoading(true)
    try {
      const res = await api.bulkConfirm(preview.valid)
      setResult(res); setStep(2)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  const reset = () => { setStep(0); setRawText(''); setPreview(null); setResult(null); setError('') }

  return (
    <Layout>
      <h1 className="page-title" style={{ marginBottom: 4 }}>Bulk Import Members</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 22 }}>
        Paste any list of email addresses. AI parsing cleans up messy input — every address is independently validated before anything is created.
      </p>

      {/* Step indicator */}
      <div className="step-track" style={{ maxWidth: 400 }}>
        {STEPS.map((s, i) => (
          <>
            {i > 0 && <div className="step-line" key={`l${i}`} />}
            <div key={s} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
              <div className={`step-dot ${i < step ? 'done' : i === step ? 'current' : ''}`}>
                {i < step ? '✓' : i + 1}
              </div>
              <div style={{ fontSize: 11, color: i === step ? 'var(--accent-text)' : 'var(--text-tertiary)', fontWeight: i === step ? 600 : 400 }}>{s}</div>
            </div>
          </>
        ))}
      </div>

      <div style={{ maxWidth: 540 }}>
        {/* Step 1: paste */}
        {step === 0 && (
          <form onSubmit={handlePreview} className="card" style={{ padding: 20 }}>
            <div className="field" style={{ marginBottom: 14 }}>
              <label className="label" htmlFor="bulk-emails">Email addresses (any format — one per line, comma-separated, etc.)</label>
              <textarea
                id="bulk-emails"
                className="input"
                rows={8}
                value={rawText}
                onChange={e => setRawText(e.target.value)}
                placeholder="alice@company.com&#10;bob@company.com&#10;carol@company.com"
              />
            </div>
            {error && <div className="alert alert-error" style={{ marginBottom: 12 }}><AlertCircle size={14} />{error}</div>}
            <button className="btn btn-primary" type="submit" disabled={loading || !rawText.trim()}>
              <ClipboardList size={14} /> {loading ? 'Parsing…' : 'Parse & Preview'}
            </button>
          </form>
        )}

        {/* Step 2: preview */}
        {step === 1 && preview && (
          <div className="card fade-in" style={{ padding: 20 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
              <span className="badge badge-success">{preview.will_create} to create</span>
              {preview.already_exists?.length > 0 && <span className="badge badge-warning">{preview.already_exists.length} already exist</span>}
              {preview.duplicates_in_batch?.length > 0 && <span className="badge badge-neutral">{preview.duplicates_in_batch.length} duplicates in list</span>}
              {preview.invalid?.length > 0 && <span className="badge badge-danger">{preview.invalid.length} invalid</span>}
            </div>

            {preview.valid.length > 0 && (
              <div style={{ maxHeight: 200, overflowY: 'auto', marginBottom: 14, display: 'flex', flexDirection: 'column', gap: 2 }}>
                {preview.valid.map(email => (
                  <div key={email} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, padding: '3px 0' }}>
                    <CheckCircle2 size={12} style={{ color: 'var(--success)', flexShrink: 0 }} />
                    {email}
                  </div>
                ))}
              </div>
            )}

            {preview.will_create === 0 && (
              <div className="alert alert-warning" style={{ marginBottom: 14 }}><AlertCircle size={14} />No new accounts to create.</div>
            )}

            {error && <div className="alert alert-error" style={{ marginBottom: 12 }}><AlertCircle size={14} />{error}</div>}

            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-secondary" onClick={() => setStep(0)}><ArrowLeft size={14} /> Back</button>
              <button className="btn btn-primary" onClick={handleConfirm} disabled={loading || preview.will_create === 0}>
                <UserPlus size={14} /> {loading ? 'Creating…' : `Create ${preview.will_create} account${preview.will_create !== 1 ? 's' : ''}`}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: done */}
        {step === 2 && result && (
          <div className="card fade-in" style={{ padding: 20 }}>
            <div className="alert alert-success" style={{ marginBottom: 14 }}>
              <CheckCircle2 size={14} />
              <span>
                {result.created.length} account{result.created.length !== 1 ? 's' : ''} created — credentials emailed to each new member.
              </span>
            </div>
            {result.failed?.length > 0 && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--danger)', marginBottom: 6 }}>Failed to create:</div>
                {result.failed.map(f => (
                  <div key={f.email} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '2px 0' }}>
                    {f.email} — {f.error}
                  </div>
                ))}
              </div>
            )}
            <button className="btn btn-secondary" onClick={reset}>Import more</button>
          </div>
        )}
      </div>
    </Layout>
  )
}
