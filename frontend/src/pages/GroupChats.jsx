import { useCallback, useEffect, useRef, useState } from 'react'
import { UsersRound, Plus, X, UserMinus, UserPlus, Download, FileText, AlertCircle, Lock, ArrowLeft } from 'lucide-react'
import { FullLayout } from '../components/Layout'
import MessageComposer from '../components/MessageComposer'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const POLL_INTERVAL = 3500

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
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

export default function GroupChats() {
  const { user } = useAuth()
  const [groups, setGroups] = useState([])
  const [active, setActive] = useState(null)
  const [messages, setMessages] = useState([])
  const [teamMembers, setTeamMembers] = useState([])
  const [groupNames, setGroupNames] = useState({})
  const [newGroupName, setNewGroupName] = useState('')
  const [selectedMembers, setSelectedMembers] = useState([])
  const [addMemberId, setAddMemberId] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [showMembers, setShowMembers] = useState(false)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [renamingGroup, setRenamingGroup] = useState(false)
  const [customNameInput, setCustomNameInput] = useState('')
  const bottomRef = useRef(null)
  const pollRef = useRef(null)
  const activeRef = useRef(active)
  activeRef.current = active

  const loadGroups = useCallback(async () => {
    try {
      const res = await api.listGroups()
      setGroups(res.groups)
    } catch {}
  }, [])

  const fetchMessages = useCallback(async (groupId) => {
    if (!groupId) return
    try {
      const res = await api.getGroupMessages(groupId)
      setMessages(res.messages)
    } catch {}
  }, [])

  const startPolling = useCallback((groupId) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(() => {
      if (activeRef.current?.group_id) fetchMessages(activeRef.current.group_id)
    }, POLL_INTERVAL)
  }, [fetchMessages])

  useEffect(() => {
    loadGroups()
    api.listTeamMembers().then(r => setTeamMembers(r.members || []))
    api.getPreferences().then(r => setGroupNames(r.group_names || {})).catch(() => {})
    return () => clearInterval(pollRef.current)
  }, [loadGroups])

  const openGroup = useCallback(async (group) => {
    setActive(group)
    setShowMembers(false)
    await fetchMessages(group.group_id)
    startPolling(group.group_id)
  }, [fetchMessages, startPolling])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const handleCreateGroup = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const group = await api.createGroup(newGroupName, selectedMembers)
      setNewGroupName(''); setSelectedMembers([]); setShowNew(false)
      await loadGroups()
      openGroup(group)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleSend = async (content) => {
    await api.sendGroupMessage(active.group_id, content)
    await fetchMessages(active.group_id)
  }

  const handleAttach = async (file) => {
    setUploading(true)
    try {
      await api.uploadFile('group', active.group_id, file)
      await fetchMessages(active.group_id)
    } finally {
      setUploading(false)
    }
  }

  const handleAddMember = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const updated = await api.addGroupMember(active.group_id, addMemberId)
      setActive(g => ({ ...g, members: updated.members }))
      setAddMemberId('')
      loadGroups()
    } catch (err) { setError(err.message) }
  }

  const handleRemoveMember = async (memberId) => {
    try {
      const updated = await api.removeGroupMember(active.group_id, memberId)
      setActive(g => ({ ...g, members: updated.members }))
      loadGroups()
    } catch (err) { setError(err.message) }
  }

  const handleDownload = async (fileId, filename) => {
    try {
      const blob = await api.downloadFile(fileId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
      URL.revokeObjectURL(url)
    } catch {}
  }

  const handleSetGroupName = async (e) => {
    e.preventDefault()
    try {
      await api.setGroupName(active.group_id, customNameInput)
      setGroupNames(n => ({ ...n, [active.group_id]: customNameInput }))
      setRenamingGroup(false)
    } catch (err) { setError(err.message) }
  }

  const toggleMember = (id) => {
    setSelectedMembers(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])
  }

  const memberMap = Object.fromEntries(teamMembers.map(m => [m.id, m.name]))
  const getGroupDisplayName = (g) => groupNames[g.group_id] ?? g.group_name
  const isCreator = active && user && active.creator_id === user.id
  const activeTitle = active ? getGroupDisplayName(active) : null

  return (
    <FullLayout>
      <style>{`
        .conv-item-hover:hover { background: var(--bg) !important; }
      `}</style>
      <div className="chat-layout-container">
        {/* Groups list */}
        <div className={`chat-sidebar-panel ${active ? 'chat-sidebar-hidden-mobile' : ''}`}>
          <div style={{ padding: '14px 14px 10px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Groups</span>
            <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setShowNew(v => !v)}>
              {showNew ? <X size={14} /> : <Plus size={14} />}
            </button>
          </div>

          {showNew && (
            <form onSubmit={handleCreateGroup} style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 8 }}>
              <input className="input input-sm" placeholder="Group name" value={newGroupName} onChange={e => setNewGroupName(e.target.value)} />
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Add members</div>
              <div style={{ maxHeight: 140, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
                {teamMembers.map(m => (
                  <label key={m.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 4px', cursor: 'pointer', fontSize: 12 }}>
                    <input type="checkbox" checked={selectedMembers.includes(m.id)} onChange={() => toggleMember(m.id)} />
                    {m.name}
                  </label>
                ))}
              </div>
              {error && <div style={{ fontSize: 11, color: 'var(--danger)' }}>{error}</div>}
              <button className="btn btn-primary btn-sm" type="submit" disabled={!newGroupName || selectedMembers.length === 0}>
                <Plus size={12} /> Create group
              </button>
            </form>
          )}

          <div style={{ flex: 1, overflowY: 'auto' }}>
            {groups.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon"><UsersRound size={18} /></div>
                <span>No groups yet</span>
              </div>
            ) : groups.map(g => (
              <button
                key={g.group_id}
                onClick={() => openGroup(g)}
                className={active?.group_id === g.group_id ? '' : 'conv-item-hover'}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                  padding: '10px 14px', border: 'none', cursor: 'pointer', textAlign: 'left',
                  borderBottom: '1px solid var(--border)',
                  background: active?.group_id === g.group_id ? 'var(--accent-subtle)' : 'transparent',
                }}
              >
                <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <UsersRound size={14} style={{ color: active?.group_id === g.group_id ? 'var(--accent)' : 'var(--text-secondary)' }} />
                </div>
                <div style={{ flex: 1, overflow: 'hidden' }}>
                  <div style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: active?.group_id === g.group_id ? 'var(--accent-text)' : 'var(--text-primary)' }}>
                    {getGroupDisplayName(g)}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{g.members?.length ?? 0} members</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Chat area */}
        <div className={`chat-main-panel ${!active ? 'chat-main-hidden-mobile' : ''}`}>
          {active ? (
            <>
              {/* Group header */}
              <div style={{ padding: '11px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10, background: 'var(--surface)' }}>
                <button
                  type="button"
                  className="btn btn-ghost btn-icon btn-sm chat-back-btn"
                  onClick={() => setActive(null)}
                  title="Back to group list"
                >
                  <ArrowLeft size={16} />
                </button>
                <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--accent-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <UsersRound size={15} style={{ color: 'var(--accent)' }} />
                </div>
                <div style={{ flex: 1 }}>
                  {renamingGroup ? (
                    <form onSubmit={handleSetGroupName} style={{ display: 'flex', gap: 6 }}>
                      <input className="input input-sm" style={{ width: 180 }} value={customNameInput} onChange={e => setCustomNameInput(e.target.value)} autoFocus />
                      <button className="btn btn-primary btn-sm" type="submit">Save</button>
                      <button className="btn btn-ghost btn-sm" type="button" onClick={() => setRenamingGroup(false)}>Cancel</button>
                    </form>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontWeight: 600, fontSize: 14 }}>{activeTitle}</span>
                      {active.group_name !== activeTitle && (
                        <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>({active.group_name})</span>
                      )}
                      <button className="btn btn-ghost btn-sm" style={{ padding: '2px 6px', fontSize: 11 }}
                        onClick={() => { setCustomNameInput(groupNames[active.group_id] ?? active.group_name); setRenamingGroup(true) }}>
                        Rename
                      </button>
                    </div>
                  )}
                </div>
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => setShowMembers(v => !v)}
                  style={{ flexShrink: 0 }}
                >
                  <UsersRound size={13} /> {active.members?.length ?? 0} members
                </button>
              </div>

              {/* Members panel (collapsible) */}
              {showMembers && (
                <div style={{ padding: '10px 20px', borderBottom: '1px solid var(--border)', background: 'var(--bg)', display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
                  {active.members?.map(m => (
                    <span key={m} className="badge badge-neutral">
                      {memberMap[m] ?? m}
                      {isCreator && m !== user?.id && (
                        <button style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'inline-flex', alignItems: 'center', color: 'var(--text-tertiary)' }}
                          onClick={() => handleRemoveMember(m)} aria-label="Remove member">
                          <X size={10} />
                        </button>
                      )}
                    </span>
                  ))}
                  {isCreator && (
                    <form onSubmit={handleAddMember} style={{ display: 'flex', gap: 4 }}>
                      <select className="input input-sm" style={{ width: 160 }} value={addMemberId} onChange={e => setAddMemberId(e.target.value)}>
                        <option value="">Add member…</option>
                        {teamMembers.filter(m => !active.members?.includes(m.id)).map(m => (
                          <option key={m.id} value={m.id}>{m.name}</option>
                        ))}
                      </select>
                      <button className="btn btn-secondary btn-sm" type="submit" disabled={!addMemberId}><UserPlus size={12} /></button>
                    </form>
                  )}
                  {error && <div style={{ fontSize: 11, color: 'var(--danger)', width: '100%' }}>{error}</div>}
                </div>
              )}

              {/* Messages */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
                {messages.map((m) => {
                  const isSelf = m.sender_id === user?.id
                  const senderName = memberMap[m.sender_id] ?? m.sender_id
                  const isFile = m.message_type === 'file'
                  return (
                    <div key={m.message_id} style={{ display: 'flex', flexDirection: 'column', alignItems: isSelf ? 'flex-end' : 'flex-start', gap: 3 }}>
                      <div className="msg-meta">{isSelf ? 'You' : senderName} · {formatTime(m.timestamp)}</div>
                      {!m.accessible ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
                          <Lock size={11} /> Message not available — sent before you joined
                        </div>
                      ) : isFile ? (
                        <FileMessageCard content={m.content} onDownload={handleDownload} />
                      ) : (
                        <div className={`msg-bubble ${isSelf ? 'msg-bubble-self' : 'msg-bubble-other'}`}>{m.content}</div>
                      )}
                    </div>
                  )
                })}
                {messages.length === 0 && (
                  <div className="empty-state" style={{ flex: 1 }}>
                    <div className="empty-state-icon"><UsersRound size={18} /></div>
                    <span>No messages yet — start the conversation!</span>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              <MessageComposer onSend={handleSend} onAttach={handleAttach} uploading={uploading} />
            </>
          ) : (
            <div className="empty-state" style={{ flex: 1 }}>
              <div className="empty-state-icon"><UsersRound size={20} /></div>
              <span style={{ fontWeight: 500 }}>Select a group</span>
              <span style={{ color: 'var(--text-tertiary)' }}>or create one with the <strong>+</strong> button</span>
            </div>
          )}
        </div>
      </div>
    </FullLayout>
  )
}
