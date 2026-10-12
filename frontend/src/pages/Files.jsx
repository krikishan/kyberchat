import { useEffect, useState } from 'react'
import { FileText, Download, AlertCircle, FolderOpen, RefreshCw, MessageSquare, UsersRound, Search } from 'lucide-react'
import Layout from '../components/Layout'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

function mimeIcon(mime) {
  if (mime?.startsWith('image/')) return '🖼'
  if (mime?.includes('pdf')) return '📄'
  if (mime?.includes('zip') || mime?.includes('tar') || mime?.includes('gz')) return '🗜'
  if (mime?.startsWith('video/')) return '🎬'
  if (mime?.startsWith('audio/')) return '🎵'
  return '📎'
}

export default function Files() {
  const { user } = useAuth()
  const [conversations, setConversations] = useState([])
  const [groups, setGroups] = useState([])
  const [teamMembers, setTeamMembers] = useState([])
  const [contactNames, setContactNames] = useState({})
  const [selectedTarget, setSelectedTarget] = useState('') // format: "conversation:<id>" or "group:<id>"
  const [manualMode, setManualMode] = useState(false)
  const [manualType, setManualType] = useState('conversation')
  const [manualId, setManualId] = useState('')
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)

  // Load chat targets on mount
  useEffect(() => {
    Promise.allSettled([
      api.listConversations(),
      api.listGroups(),
      api.listTeamMembers(),
      api.getPreferences(),
    ]).then(([cRes, gRes, mRes, pRes]) => {
      if (cRes.status === 'fulfilled') setConversations(cRes.value.conversations || [])
      if (gRes.status === 'fulfilled') setGroups(gRes.value.groups || [])
      if (mRes.status === 'fulfilled') setTeamMembers(mRes.value.members || [])
      if (pRes.status === 'fulfilled') setContactNames(pRes.value.contact_names || {})
    })
  }, [])

  const memberMap = Object.fromEntries(teamMembers.map(m => [m.id, m.name]))

  const getConvName = (c) => {
    const otherId = c.participants?.find(p => p !== user?.id)
    if (otherId && contactNames[otherId]) return contactNames[otherId]
    if (otherId && memberMap[otherId]) return memberMap[otherId]
    return c.participants?.join(', ') || 'Direct Chat'
  }

  const loadTargetFiles = async (type, id) => {
    if (!id) return
    setError('')
    setLoading(true)
    setLoaded(false)
    try {
      const res = await api.listFiles(type, id.trim())
      setFiles(res.files || [])
      setLoaded(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectChange = (e) => {
    const val = e.target.value
    setSelectedTarget(val)
    if (val) {
      const [type, id] = val.split(':')
      loadTargetFiles(type, id)
    } else {
      setFiles([])
      setLoaded(false)
    }
  }

  const handleManualSubmit = (e) => {
    e.preventDefault()
    loadTargetFiles(manualType, manualId)
  }

  const download = async (fileId, filename) => {
    try {
      const blob = await api.downloadFile(fileId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename || 'downloaded-file'
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <Layout>
      <div style={{ marginBottom: 20 }}>
        <h1 className="page-title" style={{ marginBottom: 4 }}>Files & Attachments Vault</h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          Encrypted media and document repository. When you send or receive files in chats, they are stored with post-quantum end-to-end encryption. Here you can browse and download attachments from any conversation or group without having to scroll through chat history.
        </p>
      </div>

      <div className="card" style={{ padding: 18, marginBottom: 20 }}>
        {!manualMode ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <label className="label" htmlFor="chat-target-select" style={{ marginBottom: 0 }}>
                Select Conversation or Group
              </label>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setManualMode(true)}
                style={{ fontSize: 12, padding: '2px 8px' }}
              >
                Enter custom ID
              </button>
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <select
                id="chat-target-select"
                className="input"
                style={{ flex: 1, minWidth: 240 }}
                value={selectedTarget}
                onChange={handleSelectChange}
              >
                <option value="">— Select a chat or group to view files —</option>
                {conversations.length > 0 && (
                  <optgroup label="Direct Chats">
                    {conversations.map(c => (
                      <option key={c.conversation_id} value={`conversation:${c.conversation_id}`}>
                        💬 {getConvName(c)}
                      </option>
                    ))}
                  </optgroup>
                )}
                {groups.length > 0 && (
                  <optgroup label="Groups">
                    {groups.map(g => (
                      <option key={g.group_id} value={`group:${g.group_id}`}>
                        👥 {g.group_name} ({g.members?.length || 0} members)
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
              {selectedTarget && (
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    const [type, id] = selectedTarget.split(':')
                    loadTargetFiles(type, id)
                  }}
                  disabled={loading}
                >
                  <RefreshCw size={13} className={loading ? 'spinning' : ''} /> Refresh
                </button>
              )}
            </div>
          </div>
        ) : (
          <form onSubmit={handleManualSubmit}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <span className="label" style={{ marginBottom: 0 }}>Manual Context Lookup</span>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setManualMode(false)}
                style={{ fontSize: 12, padding: '2px 8px' }}
              >
                Back to chat selector
              </button>
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
              <div className="field">
                <label className="label" htmlFor="ctx-type">Context</label>
                <select id="ctx-type" className="input" style={{ width: 150 }} value={manualType} onChange={e => setManualType(e.target.value)}>
                  <option value="conversation">Conversation</option>
                  <option value="group">Group</option>
                </select>
              </div>
              <div className="field" style={{ flex: '1 1 200px' }}>
                <label className="label" htmlFor="ctx-id">Context ID</label>
                <input id="ctx-id" className="input" value={manualId} onChange={e => setManualId(e.target.value)} placeholder="UUID string…" />
              </div>
              <button className="btn btn-primary" type="submit" disabled={!manualId.trim() || loading}>
                <FolderOpen size={14} /> Load files
              </button>
            </div>
          </form>
        )}
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 16 }}><AlertCircle size={14} />{error}</div>}

      {loaded && (
        <div className="card" style={{ overflow: 'hidden' }}>
          <div style={{
            padding: '12px 16px',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--surface-inset)'
          }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
              {files.length} {files.length === 1 ? 'file' : 'files'} shared
            </span>
          </div>

          {files.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon"><FileText size={18} /></div>
              <span>No files shared in this chat yet.</span>
              <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                Attach a file in the chat composer to share securely with post-quantum encryption.
              </span>
            </div>
          ) : files.map(f => (
            <div key={f.file_id} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '12px 16px', borderBottom: '1px solid var(--border)',
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: 8,
                background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18, flexShrink: 0,
              }}>{mimeIcon(f.mime_type)}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 500, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {f.original_filename}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                  {formatSize(f.size)} · {new Date(f.created_at).toLocaleString()}
                </div>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => download(f.file_id, f.original_filename)}
                title="Download encrypted file"
              >
                <Download size={13} /> Download
              </button>
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}
