import { useEffect, useState } from 'react'
import { UserPlus, Power, AlertCircle, CheckCircle2, Users, Trash2, X } from 'lucide-react'
import Layout from '../components/Layout'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function AdminMembers() {
  const { user } = useAuth()
  const isDev = user?.role === 'developer'

  const [members, setMembers] = useState([])
  const [teams, setTeams] = useState([])
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [selectedTeam, setSelectedTeam] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const load = async () => {
    try {
      const res = await api.listMembers()
      setMembers(res.users || [])

      if (isDev) {
        try {
          const tRes = await api.listTeams()
          setTeams(tRes.teams || [])
          if (tRes.teams?.length && !selectedTeam) {
            setSelectedTeam(tRes.teams[0].team_id)
          }
        } catch {}
      }
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => { load() }, [isDev])

  const handleAdd = async (e) => {
    e.preventDefault()
    setError(''); setSuccess('')
    setLoading(true)
    try {
      const res = await api.addMember(name, email, isDev ? selectedTeam : null)
      setSuccess(`${res.user.name} added — credentials emailed to ${res.user.email}.`)
      setName(''); setEmail('')
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const toggleStatus = async (member) => {
    const newStatus = member.status === 'active' ? 'inactive' : 'active'
    await api.setMemberStatus(member.id, newStatus)
    await load()
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    setError(''); setSuccess('')
    try {
      const res = await api.deleteUser(deleteTarget.id)
      setSuccess(res.message || `Account @${deleteTarget.username} deleted successfully.`)
      setDeleteTarget(null)
      await load()
    } catch (err) {
      setError(err.message)
      setDeleteTarget(null)
    } finally {
      setDeleting(false)
    }
  }

  const filtered = members.filter(m =>
    m.name?.toLowerCase().includes(search.toLowerCase()) ||
    m.username?.toLowerCase().includes(search.toLowerCase()) ||
    m.email?.toLowerCase().includes(search.toLowerCase()) ||
    (m.team_name && m.team_name.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <Layout>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h1 className="page-title">{isDev ? 'All Organization Members' : 'Team Members'}</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            {isDev ? 'Manage and monitor all accounts across teams.' : 'Manage members under your assigned team.'}
          </p>
        </div>
        <span className="badge badge-neutral">{members.length} member{members.length !== 1 ? 's' : ''}</span>
      </div>

      {/* Add member form */}
      <div className="card" style={{ padding: 18, marginBottom: 20 }}>
        <h2 style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>
          {isDev ? 'Add Member to Team' : 'Add Team Member'}
        </h2>
        <form onSubmit={handleAdd} style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div className="field" style={{ flex: '1 1 160px' }}>
            <label className="label" htmlFor="new-name">Full name</label>
            <input id="new-name" className="input" placeholder="e.g. Alex Morgan" value={name} onChange={e => setName(e.target.value)} required />
          </div>
          <div className="field" style={{ flex: '2 1 200px' }}>
            <label className="label" htmlFor="new-email">Email address</label>
            <input id="new-email" className="input" type="email" placeholder="alex@company.com" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          {isDev && teams.length > 0 && (
            <div className="field" style={{ flex: '1 1 180px' }}>
              <label className="label" htmlFor="team-select">Assign Team</label>
              <select id="team-select" className="input" value={selectedTeam} onChange={e => setSelectedTeam(e.target.value)}>
                {teams.map(t => (
                  <option key={t.team_id} value={t.team_id}>{t.name}</option>
                ))}
              </select>
            </div>
          )}
          <button className="btn btn-primary" type="submit" disabled={loading || !name || !email}>
            <UserPlus size={14} /> {loading ? 'Adding…' : 'Add member'}
          </button>
        </form>
        {error && <div className="alert alert-error" style={{ marginTop: 10 }}><AlertCircle size={14} />{error}</div>}
        {success && <div className="alert alert-success" style={{ marginTop: 10 }}><CheckCircle2 size={14} />{success}</div>}
      </div>

      {/* Search + list */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
          <input
            className="input input-sm"
            placeholder="Search by name, username, email, or team…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ maxWidth: 340 }}
          />
        </div>

        {filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><Users size={18} /></div>
            <span>{members.length === 0 ? 'No members found.' : 'No results match your search.'}</span>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Member</th>
                <th>Email</th>
                <th>Team</th>
                <th>Status</th>
                <th style={{ width: 170, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(m => (
                <tr key={m.id}>
                  <td>
                    <div style={{ fontWeight: 500 }}>{m.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>@{m.username}</div>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{m.email}</td>
                  <td>
                    {m.team_name ? (
                      <span className="badge badge-primary">{m.team_name}</span>
                    ) : (
                      <span className="badge badge-neutral">Unassigned</span>
                    )}
                  </td>
                  <td>
                    <span className={`badge ${m.status === 'active' ? 'badge-success' : 'badge-neutral'}`}>
                      {m.status}
                    </span>
                    {m.must_change_password && <span className="badge badge-warning" style={{ marginLeft: 6 }}>Pending login</span>}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end', alignItems: 'center' }}>
                      <button
                        className={`btn btn-sm ${m.status === 'active' ? 'btn-ghost' : 'btn-secondary'}`}
                        onClick={() => toggleStatus(m)}
                        title={m.status === 'active' ? 'Deactivate' : 'Activate'}
                      >
                        <Power size={12} />
                        {m.status === 'active' ? 'Deactivate' : 'Activate'}
                      </button>

                      {/* Deletion button - Developer can delete any, Team Lead can delete members of their team */}
                      {m.role !== 'developer' && (
                        <button
                          className="btn btn-danger btn-sm btn-icon"
                          onClick={() => setDeleteTarget(m)}
                          title="Permanently Delete Account"
                        >
                          <Trash2 size={13} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Confirm Delete Modal */}
      {deleteTarget && (
        <div className="mobile-backdrop" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 120 }}>
          <div className="card slide-up" style={{ width: '100%', maxWidth: 420, padding: 24, margin: 16, border: '1px solid var(--danger-border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--danger)', marginBottom: 12 }}>
              <Trash2 size={20} />
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                Confirm Account Deletion
              </h3>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>
              Are you sure you want to permanently delete account <strong>{deleteTarget.name}</strong> (@{deleteTarget.username})?
            </p>
            <p style={{ fontSize: 12, color: 'var(--danger)', marginBottom: 16, background: 'var(--danger-bg)', padding: '8px 10px', borderRadius: 'var(--r-sm)' }}>
              This will permanently delete their account, cryptographic keys, group chat memberships, and team assignments. This action cannot be undone.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button className="btn btn-secondary" onClick={() => setDeleteTarget(null)} disabled={deleting}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={handleDelete} disabled={deleting} style={{ background: 'var(--danger)', color: '#fff' }}>
                {deleting ? 'Deleting…' : 'Yes, Delete Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
