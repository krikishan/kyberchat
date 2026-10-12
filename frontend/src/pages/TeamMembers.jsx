import { useEffect, useState } from 'react'
import { Users, MessageSquare } from 'lucide-react'
import Layout from '../components/Layout'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function TeamMembers() {
  const { user } = useAuth()
  const [members, setMembers] = useState([])
  const [search, setSearch] = useState('')
  const [contactNames, setContactNames] = useState({})
  const [editing, setEditing] = useState(null)
  const [nameInput, setNameInput] = useState('')

  useEffect(() => {
    api.listTeamMembers().then(r => setMembers(r.members || []))
    api.getPreferences().then(r => setContactNames(r.contact_names || {})).catch(() => {})
  }, [])

  const handleSetName = async (id) => {
    try {
      await api.setContactName(id, nameInput)
      setContactNames(n => ({ ...n, [id]: nameInput }))
      setEditing(null)
    } catch {}
  }

  const handleRemoveName = async (id) => {
    await api.removeContactName(id)
    setContactNames(n => { const c = { ...n }; delete c[id]; return c })
  }

  const filtered = members.filter(m =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.username.toLowerCase().includes(search.toLowerCase())
  )

  const ROLE_LABELS = { developer: 'Developer', admin: 'Team Admin', user: 'Member' }

  return (
    <Layout>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 className="page-title">Team</h1>
        <span className="badge badge-neutral">{members.length} member{members.length !== 1 ? 's' : ''}</span>
      </div>

      <div style={{ marginBottom: 16 }}>
        <input
          className="input"
          style={{ maxWidth: 300 }}
          placeholder="Search team members…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="card" style={{ overflow: 'hidden' }}>
        {filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><Users size={18} /></div>
            <span>{members.length === 0 ? 'No team members yet.' : 'No results.'}</span>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Member</th>
                <th>Role</th>
                <th>Your name for them</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(m => (
                <tr key={m.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: '50%',
                        background: 'var(--accent-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 11, fontWeight: 700, color: 'var(--accent)', flexShrink: 0,
                      }}>{m.name[0].toUpperCase()}</div>
                      <div>
                        <div style={{ fontWeight: 500, fontSize: 13 }}>{m.name}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>@{m.username}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-neutral">{ROLE_LABELS[m.role] ?? m.role}</span>
                  </td>
                  <td>
                    {editing === m.id ? (
                      <div style={{ display: 'flex', gap: 5 }}>
                        <input
                          className="input input-sm"
                          style={{ width: 140 }}
                          value={nameInput}
                          onChange={e => setNameInput(e.target.value)}
                          autoFocus
                          placeholder="e.g. College Friend"
                        />
                        <button className="btn btn-primary btn-sm" onClick={() => handleSetName(m.id)}>Save</button>
                        <button className="btn btn-ghost btn-sm" onClick={() => setEditing(null)}>Cancel</button>
                      </div>
                    ) : (
                      <span style={{ fontSize: 13, color: contactNames[m.id] ? 'var(--text-primary)' : 'var(--text-tertiary)', fontStyle: contactNames[m.id] ? 'normal' : 'italic' }}>
                        {contactNames[m.id] ?? 'Not set'}
                      </span>
                    )}
                  </td>
                  <td>
                    {editing !== m.id && (
                      <div style={{ display: 'flex', gap: 4 }}>
                        <button className="btn btn-ghost btn-sm" onClick={() => { setEditing(m.id); setNameInput(contactNames[m.id] ?? '') }}>
                          {contactNames[m.id] ? 'Edit' : 'Set name'}
                        </button>
                        {contactNames[m.id] && (
                          <button className="btn btn-ghost btn-sm" style={{ color: 'var(--danger)' }} onClick={() => handleRemoveName(m.id)}>Remove</button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  )
}
