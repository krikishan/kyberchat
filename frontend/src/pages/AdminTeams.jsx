import { useEffect, useState } from 'react'
import {
  Users, UserPlus, Plus, Trash2, ShieldCheck, AlertCircle,
  CheckCircle2, FolderPlus, UserCheck, X, Power, Layers
} from 'lucide-react'
import Layout from '../components/Layout'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function AdminTeams() {
  const { user } = useAuth()
  const [teams, setTeams] = useState([])
  const [unassignedMembers, setUnassignedMembers] = useState([])
  const [unassignedLeads, setUnassignedLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Modals
  const [showCreateTeam, setShowCreateTeam] = useState(false)
  const [showAddLead, setShowAddLead] = useState(false)
  const [showAddMember, setShowAddMember] = useState(false)
  const [selectedTeamId, setSelectedTeamId] = useState(null)

  // Forms
  const [teamName, setTeamName] = useState('')
  const [teamDesc, setTeamDesc] = useState('')
  const [teamLeadId, setTeamLeadId] = useState('')

  const [leadName, setLeadName] = useState('')
  const [leadEmail, setLeadEmail] = useState('')
  const [leadTargetTeam, setLeadTargetTeam] = useState('')

  const [memberName, setMemberName] = useState('')
  const [memberEmail, setMemberEmail] = useState('')
  const [memberTargetTeam, setMemberTargetTeam] = useState('')

  // Deletion confirm modal
  const [deleteTarget, setDeleteTarget] = useState(null) // { type: 'user'|'team', id, name, details }

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await api.listTeams()
      setTeams(res.teams || [])
      setUnassignedMembers(res.unassigned_members || [])
      setUnassignedLeads(res.unassigned_leads || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Create Team
  const handleCreateTeam = async (e) => {
    e.preventDefault()
    setError(''); setSuccess('')
    try {
      await api.createTeam(teamName, teamDesc, teamLeadId || null)
      setSuccess(`Team "${teamName}" created successfully!`)
      setTeamName(''); setTeamDesc(''); setTeamLeadId('')
      setShowCreateTeam(false)
      await loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  // Create Team Lead
  const handleCreateLead = async (e) => {
    e.preventDefault()
    setError(''); setSuccess('')
    try {
      await api.createTeamAdmin(leadName, leadEmail, leadTargetTeam || null)
      setSuccess(`Team Lead "${leadName}" created successfully and assigned!`)
      setLeadName(''); setLeadEmail(''); setLeadTargetTeam('')
      setShowAddLead(false)
      await loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  // Add Member to specific team
  const handleAddMember = async (e) => {
    e.preventDefault()
    setError(''); setSuccess('')
    try {
      await api.addMember(memberName, memberEmail, memberTargetTeam || selectedTeamId)
      setSuccess(`Member "${memberName}" added successfully!`)
      setMemberName(''); setMemberEmail(''); setMemberTargetTeam('')
      setShowAddMember(false)
      await loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  // Confirm and execute deletion
  const executeDelete = async () => {
    if (!deleteTarget) return
    setError(''); setSuccess('')
    try {
      if (deleteTarget.type === 'team') {
        await api.deleteTeam(deleteTarget.id)
        setSuccess(`Team "${deleteTarget.name}" deleted successfully.`)
      } else if (deleteTarget.type === 'user') {
        const res = await api.deleteUser(deleteTarget.id)
        setSuccess(res.message || `Account "${deleteTarget.name}" deleted.`)
      }
      setDeleteTarget(null)
      await loadData()
    } catch (err) {
      setError(err.message)
      setDeleteTarget(null)
    }
  }

  // Toggle user status
  const toggleStatus = async (userObj) => {
    try {
      const next = userObj.status === 'active' ? 'inactive' : 'active'
      await api.setMemberStatus(userObj.id, next)
      await loadData()
    } catch (err) {
      setError(err.message)
    }
  }

  const isDev = user?.role === 'developer'

  return (
    <Layout>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 className="page-title" style={{ marginBottom: 4 }}>
            {isDev ? 'Teams & Organization Structure' : 'My Team'}
          </h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            {isDev
              ? 'Organize multiple teams, assign dedicated Team Leads, and manage respective team members.'
              : 'View and manage all members belonging to your assigned team.'}
          </p>
        </div>

        {isDev && (
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary btn-sm" onClick={() => { setError(''); setShowAddLead(true) }}>
              <ShieldCheck size={14} /> Add Team Lead
            </button>
            <button className="btn btn-primary btn-sm" onClick={() => { setError(''); setShowCreateTeam(true) }}>
              <FolderPlus size={14} /> Create Team
            </button>
          </div>
        )}
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 16 }}><AlertCircle size={14} />{error}</div>}
      {success && <div className="alert alert-success" style={{ marginBottom: 16 }}><CheckCircle2 size={14} />{success}</div>}

      {/* Teams Grid / Sections */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {teams.length === 0 && !loading && (
          <div className="card empty-state" style={{ padding: 40 }}>
            <div className="empty-state-icon"><Layers size={22} /></div>
            <span style={{ fontWeight: 600, fontSize: 14 }}>No teams created yet</span>
            <span style={{ color: 'var(--text-tertiary)', fontSize: 12 }}>
              {isDev ? 'Click "Create Team" above to establish your first organization team.' : 'You have not been assigned to a team yet.'}
            </span>
          </div>
        )}

        {teams.map((t) => (
          <div key={t.team_id} className="card" style={{ overflow: 'hidden' }}>
            {/* Team Header */}
            <div style={{
              padding: '16px 20px',
              borderBottom: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'var(--surface-inset)',
              flexWrap: 'wrap',
              gap: 10,
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{t.name}</span>
                  <span className="badge badge-primary">{t.member_count} member{t.member_count !== 1 ? 's' : ''}</span>
                </div>
                {t.description && (
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{t.description}</p>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setSelectedTeamId(t.team_id)
                    setMemberTargetTeam(t.team_id)
                    setShowAddMember(true)
                  }}
                >
                  <UserPlus size={13} /> Add Member
                </button>

                {isDev && (
                  <button
                    className="btn btn-danger btn-sm btn-icon"
                    onClick={() => setDeleteTarget({ type: 'team', id: t.team_id, name: t.name, details: 'This will delete the team and unassign all members.' })}
                    title="Delete Team"
                  >
                    <Trash2 size={13} />
                  </button>
                )}
              </div>
            </div>

            {/* Team Lead Section */}
            <div style={{
              padding: '14px 20px',
              borderBottom: '1px solid var(--border)',
              background: 'var(--surface)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 10,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{
                  width: 38, height: 38, borderRadius: 8,
                  background: 'var(--accent-subtle)', color: 'var(--accent)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 700, fontSize: 14,
                }}>
                  {t.lead ? t.lead.name[0].toUpperCase() : '?'}
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 600, fontSize: 13.5 }}>
                      {t.lead ? t.lead.name : 'No Team Lead assigned'}
                    </span>
                    <span className="badge badge-success" style={{ fontSize: 10 }}>Team Lead</span>
                    {t.lead && (
                      <span className={`badge badge-${t.lead.status === 'active' ? 'success' : 'neutral'}`} style={{ fontSize: 10 }}>
                        {t.lead.status}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                    {t.lead ? `@${t.lead.username} · ${t.lead.email}` : 'Assign an admin to lead this team'}
                  </div>
                </div>
              </div>

              {isDev && t.lead && (
                <div style={{ display: 'flex', gap: 6 }}>
                  <button
                    className="btn btn-ghost btn-sm btn-icon"
                    onClick={() => toggleStatus(t.lead)}
                    title={t.lead.status === 'active' ? 'Deactivate Lead' : 'Activate Lead'}
                  >
                    <Power size={13} style={{ color: t.lead.status === 'active' ? 'var(--success)' : 'var(--text-tertiary)' }} />
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => setDeleteTarget({ type: 'user', id: t.lead.id, name: t.lead.name, details: `Delete Team Lead account (@${t.lead.username}).` })}
                    style={{ fontSize: 11, padding: '4px 8px' }}
                  >
                    <Trash2 size={12} /> Delete Lead
                  </button>
                </div>
              )}
            </div>

            {/* Respective Team Members List */}
            <div style={{ padding: '0 20px' }}>
              <div style={{
                padding: '10px 0',
                fontSize: 11,
                fontWeight: 600,
                color: 'var(--text-tertiary)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                borderBottom: '1px solid var(--border)'
              }}>
                Team Members ({t.members.length})
              </div>

              {t.members.length === 0 ? (
                <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 12 }}>
                  No members assigned to this team yet. Use "Add Member" above to invite teammates.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  {t.members.map((m) => (
                    <div
                      key={m.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '10px 0',
                        borderBottom: '1px solid var(--border)',
                        gap: 12,
                        flexWrap: 'wrap'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 200 }}>
                        <div style={{
                          width: 30, height: 30, borderRadius: '50%',
                          background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)'
                        }}>
                          {m.name[0].toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontWeight: 500, fontSize: 13 }}>{m.name}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>@{m.username} · {m.email}</div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className={`badge badge-${m.status === 'active' ? 'success' : 'neutral'}`}>
                          {m.status}
                        </span>

                        <button
                          className="btn btn-ghost btn-sm btn-icon"
                          onClick={() => toggleStatus(m)}
                          title={m.status === 'active' ? 'Deactivate' : 'Activate'}
                        >
                          <Power size={13} style={{ color: m.status === 'active' ? 'var(--success)' : 'var(--text-tertiary)' }} />
                        </button>

                        {/* Delete member button - Allowed for Dev and Team Lead */}
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => setDeleteTarget({ type: 'user', id: m.id, name: m.name, details: `Permanently delete account for @${m.username}.` })}
                          style={{ fontSize: 11, padding: '4px 8px' }}
                        >
                          <Trash2 size={12} /> Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Developer Only: Unassigned Members Section */}
        {isDev && unassignedMembers.length > 0 && (
          <div className="card" style={{ padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 600 }}>Unassigned Members</h3>
                <p style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Members who do not belong to any specific team.</p>
              </div>
              <span className="badge badge-neutral">{unassignedMembers.length}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {unassignedMembers.map(m => (
                <div key={m.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <div>
                    <div style={{ fontWeight: 500, fontSize: 13 }}>{m.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>@{m.username} · {m.email}</div>
                  </div>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => setDeleteTarget({ type: 'user', id: m.id, name: m.name, details: `Delete unassigned account @${m.username}.` })}
                  >
                    <Trash2 size={12} /> Delete
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Modal: Create Team */}
      {showCreateTeam && (
        <div className="mobile-backdrop" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 110 }}>
          <div className="card slide-up" style={{ width: '100%', maxWidth: 440, padding: 24, margin: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <h3 style={{ fontSize: 15, fontWeight: 600 }}>Create New Team</h3>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setShowCreateTeam(false)}><X size={15} /></button>
            </div>
            <form onSubmit={handleCreateTeam} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="field">
                <label className="label">Team Name *</label>
                <input className="input" placeholder="e.g. Infrastructure & Security" value={teamName} onChange={e => setTeamName(e.target.value)} required />
              </div>
              <div className="field">
                <label className="label">Description</label>
                <input className="input" placeholder="Department purpose, scope..." value={teamDesc} onChange={e => setTeamDesc(e.target.value)} />
              </div>
              <div className="field">
                <label className="label">Assign Team Lead (Optional)</label>
                <select className="input" value={teamLeadId} onChange={e => setTeamLeadId(e.target.value)}>
                  <option value="">— Select an available Team Lead —</option>
                  {unassignedLeads.map(l => (
                    <option key={l.id} value={l.id}>{l.name} (@{l.username})</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 10 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateTeam(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={!teamName.trim()}><Plus size={14} /> Create Team</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Team Lead */}
      {showAddLead && (
        <div className="mobile-backdrop" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 110 }}>
          <div className="card slide-up" style={{ width: '100%', maxWidth: 440, padding: 24, margin: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <h3 style={{ fontSize: 15, fontWeight: 600 }}>Add New Team Lead</h3>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setShowAddLead(false)}><X size={15} /></button>
            </div>
            <form onSubmit={handleCreateLead} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="field">
                <label className="label">Full Name *</label>
                <input className="input" placeholder="e.g. Elena Rostova" value={leadName} onChange={e => setLeadName(e.target.value)} required />
              </div>
              <div className="field">
                <label className="label">Email Address *</label>
                <input className="input" type="email" placeholder="elena@company.com" value={leadEmail} onChange={e => setLeadEmail(e.target.value)} required />
              </div>
              <div className="field">
                <label className="label">Assign to Team</label>
                <select className="input" value={leadTargetTeam} onChange={e => setLeadTargetTeam(e.target.value)}>
                  <option value="">— Unassigned (Assign later) —</option>
                  {teams.map(t => (
                    <option key={t.team_id} value={t.team_id}>{t.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 10 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddLead(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={!leadName.trim() || !leadEmail.trim()}>
                  <ShieldCheck size={14} /> Create Team Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Add Member to Team */}
      {showAddMember && (
        <div className="mobile-backdrop" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 110 }}>
          <div className="card slide-up" style={{ width: '100%', maxWidth: 440, padding: 24, margin: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <h3 style={{ fontSize: 15, fontWeight: 600 }}>Add Member to Team</h3>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setShowAddMember(false)}><X size={15} /></button>
            </div>
            <form onSubmit={handleAddMember} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div className="field">
                <label className="label">Full Name *</label>
                <input className="input" placeholder="e.g. David Vance" value={memberName} onChange={e => setMemberName(e.target.value)} required />
              </div>
              <div className="field">
                <label className="label">Email Address *</label>
                <input className="input" type="email" placeholder="david@company.com" value={memberEmail} onChange={e => setMemberEmail(e.target.value)} required />
              </div>
              {isDev && (
                <div className="field">
                  <label className="label">Target Team</label>
                  <select className="input" value={memberTargetTeam} onChange={e => setMemberTargetTeam(e.target.value)}>
                    {teams.map(t => (
                      <option key={t.team_id} value={t.team_id}>{t.name}</option>
                    ))}
                  </select>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 10 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddMember(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={!memberName.trim() || !memberEmail.trim()}>
                  <UserPlus size={14} /> Add Member
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Confirmation for Deletion */}
      {deleteTarget && (
        <div className="mobile-backdrop" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 120 }}>
          <div className="card slide-up" style={{ width: '100%', maxWidth: 420, padding: 24, margin: 16, border: '1px solid var(--danger-border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--danger)', marginBottom: 12 }}>
              <Trash2 size={20} />
              <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                Confirm Permanent Deletion
              </h3>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>
              Are you sure you want to delete <strong>{deleteTarget.name}</strong>?
            </p>
            {deleteTarget.details && (
              <p style={{ fontSize: 12, color: 'var(--danger)', marginBottom: 16, background: 'var(--danger-bg)', padding: '8px 10px', borderRadius: 'var(--r-sm)' }}>
                {deleteTarget.details}
              </p>
            )}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button className="btn btn-secondary" onClick={() => setDeleteTarget(null)}>Cancel</button>
              <button className="btn btn-danger" onClick={executeDelete} style={{ background: 'var(--danger)', color: '#fff' }}>
                Yes, Permanently Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
