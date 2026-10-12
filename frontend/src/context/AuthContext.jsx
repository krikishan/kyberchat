import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { api, setToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const me = await api.me()
      setUser(me)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const onUnauthorized = () => setUser(null)
    window.addEventListener('kc:unauthorized', onUnauthorized)
    return () => window.removeEventListener('kc:unauthorized', onUnauthorized)
  }, [refresh])

  const login = async (username, password) => {
    const result = await api.login(username, password)
    setToken(result.token)
    setUser(result.user)
    return result.user
  }

  const logout = async () => {
    try { await api.logout() } catch { /* ignore */ }
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
