import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import {
  clearTokens,
  refreshAccess,
  setAccessToken,
  setAuthLostHandler,
  setRefreshToken,
} from '../api/client.js'
import { getMe } from '../api/auth.js'

const AuthContext = createContext(null)

// Провайдер авторизации: хранит текущего пользователя и восстанавливает сессию
// при загрузке приложения по refresh-токену из localStorage.
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Когда обновить токен не удалось — сбрасываем пользователя.
    setAuthLostHandler(() => setUser(null))

    let cancelled = false
    refreshAccess().then(async (ok) => {
      if (ok) {
        try {
          const { data } = await getMe()
          if (!cancelled) setUser(data)
        } catch {
          if (!cancelled) clearTokens()
        }
      }
      if (!cancelled) setLoading(false)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(({ access, refresh, user: profile }) => {
    setAccessToken(access)
    setRefreshToken(refresh)
    setUser(profile)
  }, [])

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
  }, [])

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    isGuest: Boolean(user?.is_guest),
    login,
    logout,
    updateUser: setUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth должен использоваться внутри AuthProvider')
  }
  return ctx
}
