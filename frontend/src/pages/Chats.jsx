import { useCallback, useEffect, useRef, useState } from 'react'
import { MessageSquare, Plus, X, Download, FileText, Users, AlertCircle, ArrowLeft } from 'lucide-react'
import { FullLayout } from '../components/Layout'
import MessageComposer from '../components/MessageComposer'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const POLL_INTERVAL = 3500 // ms

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function FileMessageCard({ content, onDownload }) {
  let meta = {}
  try { meta = JSON.parse(content) } catch { return null }
  return (
    <div className="file-card">
      <div className="file-card-icon"><FileText size={15} /></div>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <div style={{ fontWeight: 500, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {meta.filename || 'File'}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{formatSize(meta.size)} · {meta.mime_type}</div>
      </div>
      {meta.file_id && (
        <button className="btn btn-ghost btn-icon btn-sm" onClick={() => onDownload(meta.file_id, meta.filename)} title="Download">
          <Download size={13} />
        </button>
      )}
    </div>
  )
}

function Avatar({ name, size = 32 }) {
  const initial = (name || '?')[0].toUpperCase()
  const colors = ['#e0e7ff', '#fce7f3', '#d1fae5', '#fef3c7', '#fee2e2', '#ede9fe']
  const ci = initial.charCodeAt(0) % colors.length
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%',
      background: colors[ci], display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * 0.38, fontWeight: 600, color: 'var(--text-secondary)', flexShrink: 0,
    }}>{initial}</div>
  )
}

function ConversationItem({ conv, isActive, onClick, names, memberMap }) {
  const customAlias = names?.[conv.other_user_id]
  const directoryName = memberMap?.[conv.other_user_id] || conv.other_user_name
  const username = conv.other_username ? `@${conv.other_username}` : ''
  const displayName = customAlias || directoryName || (username ? username : 'Direct Chat')

  return (
    <button
      onClick={onClick}
      style={{
        width: '100%', display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 14px', border: 'none', background: isActive ? 'var(--accent-subtle)' : 'transparent',
        cursor: 'pointer', textAlign: 'left', borderBottom: '1px solid var(--border)',
        transition: 'background var(--t-fast)',
      }}
      className={isActive ? '' : 'conv-item-hover'}
    >
      <Avatar name={displayName} />
      <div style={{ flex: 1, minWidth: 0, overflow: 'hidden' }}>
        <div style={{
          fontSize: 13,
          fontWeight: 500,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          color: isActive ? 'var(--accent-text)' : 'var(--text-primary)',
        }}>
          {displayName}
        </div>
        {username && (
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {username}
          </div>
        )}
      </div>
    </button>
  )
}

export default function Chats() {
  const { user } = useAuth()
  const [conversations, setConversations] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([])
  const [teamMembers, setTeamMembers] = useState([])
  const [contactNames, setContactNames] = useState({})
  const [newUserId, setNewUserId] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const bottomRef = useRef(null)
  const pollRef = useRef(null)
  const activeIdRef = useRef(activeId)
  activeIdRef.current = activeId

  const loadConversations = useCallback(async () => {
    try {
      const res = await api.listConversations()
      setConversations(res.conversations)
    } catch {}
  }, [])

  const fetchMessages = useCallback(async (id) => {
    if (!id) return
    try {
      const res = await api.getMessages(id)
      setMessages(res.messages)
    } catch {}
  }, [])

  const startPolling = useCallback((id) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(() => fetchMessages(activeIdRef.current), POLL_INTERVAL)
  }, [fetchMessages])

  useEffect(() => {
    loadConversations()
    api.listTeamMembers().then(r => setTeamMembers(r.members || []))
    api.getPreferences().then(r => setContactNames(r.contact_names || {})).catch(() => {})
    return () => clearInterval(pollRef.current)
  }, [loadConversations])

  const openConversation = useCallback(async (id) => {
    setActiveId(id)
    await fetchMessages(id)
    startPolling(id)
  }, [fetchMessages, startPolling])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleStartConversation = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const conv = await api.createConversation(newUserId.trim())
      setNewUserId('')
      setShowNew(false)
      await loadConversations()
      openConversation(conv.conversation_id)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleSend = async (content) => {
    await api.sendMessage(activeId, content)
    await fetchMessages(activeId)
  }

  const handleAttach = async (file) => {
    setUploading(true)
    try {
      await api.uploadFile('conversation', activeId, file)
      await fetchMessages(activeId)
    } catch (err) {
      console.error('Upload failed:', err.message)
    } finally {
      setUploading(false)
    }
  }

  const handleDownload = async (fileId, filename) => {
    try {
      const blob = await api.downloadFile(fileId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = filename; a.click()
      URL.revokeObjectURL(url)
    } catch {}
  }

  const memberMap = Object.fromEntries(teamMembers.map(m => [m.id, m.name]))

  const getDisplayName = (conv) => {
    if (!conv) return 'Select a conversation'
    const otherId = conv.other_user_id || conv.participants?.find(p => p !== user?.id)
    if (otherId && contactNames[otherId]) return contactNames[otherId]
    if (conv.other_user_name && conv.other_user_name !== 'Secure Contact') return conv.other_user_name
    if (otherId && memberMap[otherId]) return memberMap[otherId]
    if (conv.other_username) return `@${conv.other_username}`
    return conv.other_user_name || 'Direct Chat'
  }

  const activeConv = conversations.find(c => c.conversation_id === activeId)
  const activeTitle = activeConv ? getDisplayName(activeConv) : 'Select a conversation'

  return (
    <FullLayout>
      <style>{`
        .conv-item-hover:hover { background: var(--bg) !important; }
      `}</style>
      <div className="chat-layout-container">
        {/* Sidebar panel */}
        <div className={`chat-sidebar-panel ${activeId ? 'chat-sidebar-hidden-mobile' : ''}`}>
          {/* Header */}
          <div style={{ padding: '14px 14px 10px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Chats</span>
            <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setShowNew(v => !v)} title="New conversation">
              {showNew ? <X size={14} /> : <Plus size={14} />}
            </button>
          </div>

          {/* New conv form */}
          {showNew && (
            <form onSubmit={handleStartConversation} style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 6 }}>
              <select
                className="input input-sm"
                style={{ flex: 1 }}
                value={newUserId}
                onChange={e => setNewUserId(e.target.value)}
              >
                <option value="">Select team member…</option>
                {teamMembers.map(m => (
                  <option key={m.id} value={m.id}>{m.name} (@{m.username})</option>
                ))}
              </select>
              <button className="btn btn-primary btn-sm" type="submit" disabled={!newUserId}>Start</button>
            </form>
          )}
          {error && <div className="alert alert-error" style={{ margin: '0 12px 8px', fontSize: 12 }}><AlertCircle size={12} />{error}</div>}

          {/* List */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {conversations.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon"><MessageSquare size={18} /></div>
                <span>No conversations yet</span>
              </div>
            ) : conversations.map(c => {
              const otherId = c.other_user_id || c.participants?.find(p => p !== user?.id)
              return (
                <ConversationItem
                  key={c.conversation_id}
                  conv={{ ...c, other_user_id: otherId }}
                  isActive={activeId === c.conversation_id}
                  onClick={() => openConversation(c.conversation_id)}
                  names={contactNames}
                  memberMap={memberMap}
                />
              )
            })}
          </div>
        </div>

        {/* Chat area */}
        <div className={`chat-main-panel ${!activeId ? 'chat-main-hidden-mobile' : ''}`}>
          {activeId ? (
            <>
              {/* Chat header */}
              <div style={{
                padding: '13px 20px', borderBottom: '1px solid var(--border)',
                display: 'flex', alignItems: 'center', gap: 10, background: 'var(--surface)',
              }}>
                <button
                  type="button"
                  className="btn btn-ghost btn-icon btn-sm chat-back-btn"
                  onClick={() => setActiveId(null)}
                  title="Back to conversations"
                >
                  <ArrowLeft size={16} />
                </button>
                <Avatar name={activeTitle} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{activeTitle}</div>
                </div>
              </div>

              {/* Messages */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
                {messages.map((m) => {
                  const isSelf = m.sender_id === user?.id
                  const senderName = memberMap[m.sender_id] ?? m.sender_id
                  const isFile = m.message_type === 'file'
                  return (
                    <div key={m.message_id} style={{ display: 'flex', flexDirection: 'column', alignItems: isSelf ? 'flex-end' : 'flex-start', gap: 3 }}>
                      <div className="msg-meta">{isSelf ? 'You' : senderName} · {formatTime(m.timestamp)}</div>
                      {isFile
                        ? <FileMessageCard content={m.content} onDownload={handleDownload} />
                        : <div className={`msg-bubble ${isSelf ? 'msg-bubble-self' : 'msg-bubble-other'}`}>{m.content}</div>
                      }
                    </div>
                  )
                })}
                {messages.length === 0 && (
                  <div className="empty-state" style={{ flex: 1 }}>
                    <div className="empty-state-icon"><MessageSquare size={18} /></div>
                    <span>No messages yet — say hello!</span>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              <MessageComposer onSend={handleSend} onAttach={handleAttach} uploading={uploading} />
            </>
          ) : (
            <div className="empty-state" style={{ flex: 1 }}>
              <div className="empty-state-icon"><MessageSquare size={20} /></div>
              <span style={{ fontWeight: 500 }}>Select a conversation</span>
              <span style={{ color: 'var(--text-tertiary)' }}>or start a new one with the <strong>+</strong> button</span>
            </div>
          )}
        </div>
      </div>
    </FullLayout>
  )
}
