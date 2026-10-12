import { useEffect, useRef, useState } from 'react'
import { Sparkles, Send, Paperclip, X, Check, Pencil, AlertCircle, FileText } from 'lucide-react'
import { api } from '../api/client'

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function MessageComposer({ onSend, onAttach, uploading }) {
  const [text, setText] = useState('')
  const [style, setStyle] = useState('clear')
  const [enhancing, setEnhancing] = useState(false)
  const [suggestion, setSuggestion] = useState(null)
  const [aiError, setAiError] = useState('')
  const [pendingFile, setPendingFile] = useState(null)
  const fileRef = useRef(null)
  const textRef = useRef(null)

  const handleEnhance = async () => {
    if (!text.trim()) return
    setAiError('')
    setEnhancing(true)
    setSuggestion(null)
    try {
      const result = await api.enhance(text, style)
      setSuggestion(result)
    } catch (e) {
      setAiError(e.message)
    } finally {
      setEnhancing(false)
    }
  }

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed && !pendingFile) return
    if (pendingFile && onAttach) {
      onAttach(pendingFile)
      setPendingFile(null)
    }
    if (trimmed) {
      onSend(trimmed)
      setText('')
    }
    setSuggestion(null)
    setAiError('')
    textRef.current?.focus()
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const acceptSuggestion = () => {
    setText(suggestion.enhanced)
    setSuggestion(null)
    textRef.current?.focus()
  }

  const editSuggestion = () => {
    setText(suggestion.enhanced)
    setSuggestion(null)
  }

  const onFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) setPendingFile(file)
    e.target.value = ''
  }

  const canSend = text.trim() || pendingFile

  return (
    <div style={{
      borderTop: '1px solid var(--border)',
      background: 'var(--surface)',
      flexShrink: 0,
    }}>
      {/* AI suggestion panel */}
      {suggestion && (
        <div className="slide-up" style={{
          margin: '10px 14px 0',
          padding: '12px 14px',
          borderRadius: 'var(--r-md)',
          background: 'var(--bg)',
          border: '1px solid var(--border)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <Sparkles size={12} style={{ color: 'var(--accent)' }} />
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              AI suggestion · {suggestion.style}
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', textDecoration: 'line-through', marginBottom: 4 }}>
            {suggestion.original}
          </div>
          <div style={{ fontSize: 14, color: 'var(--text-primary)', marginBottom: 10, lineHeight: 1.5 }}>
            {suggestion.enhanced}
          </div>
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn btn-primary btn-sm" onClick={acceptSuggestion}>
              <Check size={12} /> Accept
            </button>
            <button className="btn btn-secondary btn-sm" onClick={editSuggestion}>
              <Pencil size={12} /> Edit
            </button>
            <button className="btn btn-ghost btn-sm" onClick={() => setSuggestion(null)}>
              <X size={12} /> Dismiss
            </button>
          </div>
        </div>
      )}

      {/* AI error */}
      {aiError && (
        <div style={{ margin: '8px 14px 0', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--danger)' }}>
          <AlertCircle size={12} />
          <span>{aiError}</span>
          <button style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setAiError('')}>✕</button>
        </div>
      )}

      {/* Pending file preview */}
      {pendingFile && (
        <div style={{ margin: '8px 14px 0', display: 'flex', alignItems: 'center', gap: 8, padding: '7px 10px', background: 'var(--accent-subtle)', borderRadius: 'var(--r-sm)', border: '1px solid #c7d2fe' }}>
          <FileText size={13} style={{ color: 'var(--accent)', flexShrink: 0 }} />
          <span style={{ fontSize: 12, fontWeight: 500, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--accent-text)' }}>
            {pendingFile.name}
          </span>
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)', flexShrink: 0 }}>
            {formatSize(pendingFile.size)}
          </span>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setPendingFile(null)} aria-label="Remove file">
            <X size={12} />
          </button>
        </div>
      )}

      {/* Composer row */}
      <div style={{ display: 'flex', gap: 6, alignItems: 'flex-end', padding: '10px 14px' }}>
        {onAttach && (
          <>
            <input ref={fileRef} type="file" hidden onChange={onFileChange} />
            <button
              className="btn btn-secondary btn-icon"
              onClick={() => fileRef.current?.click()}
              aria-label="Attach file"
              disabled={uploading}
              title="Attach file"
            >
              <Paperclip size={15} />
            </button>
          </>
        )}

        <textarea
          ref={textRef}
          className="input"
          rows={1}
          placeholder="Write a message…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          style={{ resize: 'none', minHeight: 38, maxHeight: 120, flex: 1, overflowY: 'auto', lineHeight: 1.5 }}
        />

        {/* AI style + enhance button */}
        <div style={{ display: 'flex', gap: 4, alignItems: 'stretch' }}>
          <select
            className="input input-sm"
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            style={{ width: 100 }}
            aria-label="Enhancement style"
          >
            <option value="clear">Clear</option>
            <option value="professional">Professional</option>
            <option value="formal">Formal</option>
            <option value="friendly">Friendly</option>
            <option value="concise">Concise</option>
          </select>
          <button
            className="btn btn-secondary btn-icon"
            onClick={handleEnhance}
            disabled={enhancing || !text.trim()}
            title={enhancing ? 'Enhancing…' : 'Enhance with AI'}
            aria-label="Enhance with AI"
          >
            <Sparkles size={15} style={{ color: enhancing ? 'var(--accent)' : 'inherit', animation: enhancing ? 'kcSpin 900ms linear infinite' : 'none' }} />
          </button>
        </div>

        <button
          className="btn btn-primary btn-icon"
          onClick={handleSend}
          disabled={!canSend || uploading}
          aria-label="Send message"
          title="Send (Enter)"
        >
          <Send size={15} />
        </button>
      </div>

      <style>{`
        @keyframes kcSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
