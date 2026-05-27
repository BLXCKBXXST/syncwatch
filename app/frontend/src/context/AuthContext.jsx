import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import {
  clearTokens,
  refreshAccess,
  setAccessToken,
  setAuthLostHandler,
  setRefreshToken,
} from '../api/client.js'
import { getMe, logoutAll as apiLogoutAll } from '../api/auth.js'

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

  // Инвалидирует все refresh-токены на бэке и разлогинивает локально.
  // Чужие сессии получат 401 при ближайшем refresh access-токена.
  const logoutEverywhere = useCallback(async () => {
    try {
      await apiLogoutAll()
    } catch {
      // молча: даже если запрос упал, локально разлогинимся
    }
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
    logoutEverywhere,
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
