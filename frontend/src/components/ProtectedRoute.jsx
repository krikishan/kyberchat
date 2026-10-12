import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const ROLE_LEVEL = { developer: 3, admin: 2, user: 1 }

export function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return children
}

/** Accessible by admin and developer */
export function AdminRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if ((ROLE_LEVEL[user.role] ?? 0) < ROLE_LEVEL.admin) return <Navigate to="/" replace />
  return children
}

/** Accessible by developer only */
export function DeveloperRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'developer') return <Navigate to="/" replace />
  return children
}
