import { useState } from 'react'
import { Sparkles, Check, X, AlertCircle, Pencil } from 'lucide-react'
import Layout from '../components/Layout'
import { api } from '../api/client'

const STYLE_DESCRIPTIONS = {
  professional: 'Maintains a business-appropriate tone while preserving your message.',
  formal:       'Structures the message for formal documents or official communication.',
  friendly:     'Makes the message feel warm and approachable.',
  concise:      'Trims the message to its essential meaning.',
  clear:        'Improves clarity and readability without changing the meaning.',
}

export default function AIEnhancerPage() {
  const [text, setText] = useState('')
  const [style, setStyle] = useState('professional')
  const [enhancing, setEnhancing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleEnhance = async () => {
    setError(''); setEnhancing(true); setResult(null)
    try {
      const res = await api.enhance(text, style)
      setResult(res)
    } catch (e) { setError(e.message) }
    finally { setEnhancing(false) }
  }

  return (
    <Layout>
      <h1 className="page-title" style={{ marginBottom: 4 }}>AI Message Enhancer</h1>
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24 }}>
        Draft a message, then choose how to refine it. The original is never changed automatically — you decide what to use.
      </p>

      <div style={{ maxWidth: 640 }}>
        {/* Input card */}
        <div className="card" style={{ padding: 18, marginBottom: 12 }}>
          <div className="field" style={{ marginBottom: 14 }}>
            <label className="label" htmlFor="ai-text">Your message</label>
            <textarea
              id="ai-text"
              className="input"
              rows={4}
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Type your draft here…"
            />
          </div>

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div className="field" style={{ flex: '0 0 180px' }}>
              <label className="label" htmlFor="ai-style">Enhancement style</label>
              <select id="ai-style" className="input" value={style} onChange={e => setStyle(e.target.value)}>
                {Object.keys(STYLE_DESCRIPTIONS).map(s => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1, fontSize: 12, color: 'var(--text-secondary)', paddingBottom: 8 }}>
              {STYLE_DESCRIPTIONS[style]}
            </div>
          </div>

          <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <button
              className="btn btn-primary"
              onClick={handleEnhance}
              disabled={enhancing || !text.trim()}
            >
              <Sparkles size={14} style={{ animation: enhancing ? 'kcSpin 900ms linear infinite' : 'none' }} />
              {enhancing ? 'Enhancing…' : 'Enhance'}
            </button>
            {(result || error) && (
              <button className="btn btn-ghost" onClick={() => { setResult(null); setError('') }}>
                <X size={14} /> Clear result
              </button>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="alert alert-error fade-in" style={{ marginBottom: 12 }}>
            <AlertCircle size={14} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="card fade-in" style={{ padding: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 16 }}>
              <Sparkles size={14} style={{ color: 'var(--accent)' }} />
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Enhancement Result · {result.style}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Original</div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, background: 'var(--bg)', padding: '10px 12px', borderRadius: 'var(--r-sm)', border: '1px solid var(--border)' }}>
                  {result.original}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Enhanced</div>
                <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.6, background: 'var(--accent-subtle)', padding: '10px 12px', borderRadius: 'var(--r-sm)', border: '1px solid #c7d2fe' }}>
                  {result.enhanced}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary" onClick={() => { setText(result.enhanced); setResult(null) }}>
                <Check size={14} /> Use this
              </button>
              <button className="btn btn-secondary" onClick={() => { setText(result.enhanced); setResult(null) }}>
                <Pencil size={14} /> Edit before using
              </button>
              <button className="btn btn-ghost" onClick={() => setResult(null)}>
                <X size={14} /> Dismiss
              </button>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes kcSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </Layout>
  )
}
