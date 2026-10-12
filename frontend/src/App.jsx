import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ProtectedRoute, AdminRoute, DeveloperRoute } from './components/ProtectedRoute'

import Login from './pages/Login'
import ChangePassword from './pages/ChangePassword'
import Home from './pages/Home'
import Profile from './pages/Profile'
import Chats from './pages/Chats'
import GroupChats from './pages/GroupChats'
import Files from './pages/Files'
import TeamMembers from './pages/TeamMembers'
import AIEnhancerPage from './pages/AIEnhancerPage'
import Simulation from './pages/Simulation'
import Performance from './pages/Performance'
import Health from './pages/Health'
import AdminDashboard from './pages/AdminDashboard'
import AdminMembers from './pages/AdminMembers'
import AdminBulkAdd from './pages/AdminBulkAdd'
import AdminTeams from './pages/AdminTeams'

const ROLE_LEVEL = { developer: 3, admin: 2, user: 1 }

function RoleHome() {
  const { user } = useAuth()
  if (!user) return null
  if ((ROLE_LEVEL[user.role] ?? 0) >= ROLE_LEVEL.admin) return <Navigate to="/admin" replace />
  return <Home />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* All authenticated users */}
          <Route path="/"               element={<ProtectedRoute><RoleHome /></ProtectedRoute>} />
          <Route path="/change-password" element={<ProtectedRoute><ChangePassword /></ProtectedRoute>} />
          <Route path="/profile"         element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/chats"           element={<ProtectedRoute><Chats /></ProtectedRoute>} />
          <Route path="/groups"          element={<ProtectedRoute><GroupChats /></ProtectedRoute>} />
          <Route path="/files"           element={<ProtectedRoute><Files /></ProtectedRoute>} />
          <Route path="/members"         element={<ProtectedRoute><TeamMembers /></ProtectedRoute>} />
          <Route path="/ai"             element={<ProtectedRoute><AIEnhancerPage /></ProtectedRoute>} />

          {/* Admin + Developer */}
          <Route path="/admin"          element={<AdminRoute><AdminDashboard /></AdminRoute>} />
          <Route path="/admin/teams"    element={<AdminRoute><AdminTeams /></AdminRoute>} />
          <Route path="/admin/members"  element={<AdminRoute><AdminMembers /></AdminRoute>} />
          <Route path="/admin/bulk-add" element={<AdminRoute><AdminBulkAdd /></AdminRoute>} />

          {/* Developer only */}
          <Route path="/simulation"  element={<DeveloperRoute><Simulation /></DeveloperRoute>} />
          <Route path="/performance" element={<DeveloperRoute><Performance /></DeveloperRoute>} />
          <Route path="/health"      element={<DeveloperRoute><Health /></DeveloperRoute>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
