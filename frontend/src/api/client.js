const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000'

function getToken() {
  return sessionStorage.getItem('kc_token')
}

export function setToken(token) {
  if (token) sessionStorage.setItem('kc_token', token)
  else sessionStorage.removeItem('kc_token')
}

async function request(path, { method = 'GET', body, isForm = false, isBlob = false } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (!isForm && body !== undefined) headers['Content-Type'] = 'application/json'

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401) {
    setToken(null)
    window.dispatchEvent(new CustomEvent('kc:unauthorized'))
  }

  if (isBlob) {
    if (!res.ok) throw new Error('Download failed.')
    return res.blob()
  }

  let data = null
  try {
    data = await res.json()
  } catch {
    // no body
  }

  if (!res.ok) {
    throw new Error(data?.error || 'Something went wrong. Please try again.')
  }
  return data
}

export const api = {
  // Auth
  login: (username, password) => request('/api/auth/login', { method: 'POST', body: { username, password } }),
  logout: () => request('/api/auth/logout', { method: 'POST' }),
  me: () => request('/api/auth/me'),
  changePassword: (current_password, new_password) =>
    request('/api/auth/change-password', { method: 'POST', body: { current_password, new_password } }),

  // Admin & Teams
  addMember: (name, email, team_id) => request('/api/admin/users', { method: 'POST', body: { name, email, team_id } }),
  listMembers: (team_id) => request(team_id ? `/api/admin/users?team_id=${team_id}` : '/api/admin/users'),
  setMemberStatus: (id, status) => request(`/api/admin/users/${id}`, { method: 'PATCH', body: { status } }),
  deleteUser: (id) => request(`/api/admin/users/${id}`, { method: 'DELETE' }),
  listTeams: () => request('/api/admin/teams'),
  createTeam: (name, description, lead_id) => request('/api/admin/teams', { method: 'POST', body: { name, description, lead_id } }),
  updateTeam: (id, data) => request(`/api/admin/teams/${id}`, { method: 'PUT', body: data }),
  deleteTeam: (id) => request(`/api/admin/teams/${id}`, { method: 'DELETE' }),
  bulkPreview: (raw_text) => request('/api/admin/users/bulk/preview', { method: 'POST', body: { raw_text } }),
  bulkConfirm: (emails, names, team_id) => request('/api/admin/users/bulk/confirm', { method: 'POST', body: { emails, names, team_id } }),

  // Conversations
  listConversations: () => request('/api/conversations'),
  createConversation: (user_id) => request('/api/conversations', { method: 'POST', body: { user_id } }),
  getMessages: (conversationId) => request(`/api/conversations/${conversationId}/messages`),
  sendMessage: (conversationId, content) =>
    request(`/api/conversations/${conversationId}/messages`, { method: 'POST', body: { content } }),

  // Groups
  listGroups: () => request('/api/groups'),
  createGroup: (group_name, member_ids) => request('/api/groups', { method: 'POST', body: { group_name, member_ids } }),
  getGroup: (groupId) => request(`/api/groups/${groupId}`),
  addGroupMember: (groupId, user_id) => request(`/api/groups/${groupId}/members`, { method: 'POST', body: { user_id } }),
  removeGroupMember: (groupId, userId) => request(`/api/groups/${groupId}/members/${userId}`, { method: 'DELETE' }),
  getGroupMessages: (groupId) => request(`/api/groups/${groupId}/messages`),
  sendGroupMessage: (groupId, content) => request(`/api/groups/${groupId}/messages`, { method: 'POST', body: { content } }),

  // Files
  uploadFile: (contextType, contextId, file) => {
    const form = new FormData()
    form.append('file', file)
    form.append('context_type', contextType)
    form.append('context_id', contextId)
    return request('/api/files', { method: 'POST', body: form, isForm: true })
  },
  listFiles: (contextType, contextId) => request(`/api/files?context_type=${contextType}&context_id=${contextId}`),
  downloadFile: (fileId) => request(`/api/files/${fileId}/download`, { isBlob: true }),

  // Team
  listTeamMembers: () => request('/api/team/members'),

  // Preferences (personal contact/group names)
  getPreferences: () => request('/api/preferences'),
  setContactName: (contactId, name) => request(`/api/preferences/contacts/${contactId}`, { method: 'PUT', body: { name } }),
  removeContactName: (contactId) => request(`/api/preferences/contacts/${contactId}`, { method: 'DELETE' }),
  setGroupName: (groupId, name) => request(`/api/preferences/groups/${groupId}`, { method: 'PUT', body: { name } }),
  removeGroupName: (groupId) => request(`/api/preferences/groups/${groupId}`, { method: 'DELETE' }),

  // Developer — team admin management
  listTeamAdmins: () => request('/api/admin/team-admins'),
  createTeamAdmin: (name, email, team_id) => request('/api/admin/team-admins', { method: 'POST', body: { name, email, team_id } }),
  setAdminStatus: (id, status) => request(`/api/admin/team-admins/${id}`, { method: 'PATCH', body: { status } }),

  // AI
  enhance: (text, style) => request('/api/ai/enhance', { method: 'POST', body: { text, style } }),
  enhanceStyles: () => request('/api/ai/enhance/styles'),

  // Crypto / performance / health
  runSimulation: (message) => request('/api/crypto/simulation', { method: 'POST', body: { message } }),
  cryptoSelfTest: () => request('/api/crypto/test', { method: 'POST' }),
  getPerformance: () => request('/api/performance'),
  runBenchmark: (trials) => request('/api/performance/run', { method: 'POST', body: { trials } }),
  getHealth: () => request('/api/health'),
}
