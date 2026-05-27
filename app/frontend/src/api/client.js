import axios from 'axios'

// Базовый URL относительный: в разработке его проксирует Vite, в продакшене —
// Caddy (тот же origin). Переопределяется через VITE_API_BASE при необходимости.
const baseURL = import.meta.env.VITE_API_BASE || '/api'
const REFRESH_KEY = 'blxckhub_refresh'

// Access-токен хранится только в памяти; refresh-токен — в localStorage.
let accessToken = null
let onAuthLost = () => {}

export function setAccessToken(token) {
  accessToken = token || null
}

// Текущий access-токен нужен для авторизации WebSocket-соединения (query-параметр).
export function getAccessToken() {
  return accessToken
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY)
}

export function setRefreshToken(token) {
  if (token) localStorage.setItem(REFRESH_KEY, token)
  else localStorage.removeItem(REFRESH_KEY)
}

export function clearTokens() {
  accessToken = null
  localStorage.removeItem(REFRESH_KEY)
}

// Вызывается, когда сессию восстановить не удалось (требуется повторный вход).
export function setAuthLostHandler(handler) {
  onAuthLost = handler
}

const client = axios.create({ baseURL })

// Экземпляр без интерсепторов — для запроса refresh, чтобы не зациклить 401.
const bare = axios.create({ baseURL })

// Запрос: подставляем access-токен.
client.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// Ответ: на 401 один раз пробуем обновить access-токен и повторить запрос.
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true
      if (await refreshAccess()) {
        original.headers.Authorization = `Bearer ${accessToken}`
        return client(original)
      }
      clearTokens()
      onAuthLost()
    }
    return Promise.reject(error)
  },
)

// Обновляет access-токен по refresh-токену. true — успех, false — сессия потеряна.
export async function refreshAccess() {
  const refresh = getRefreshToken()
  if (!refresh) return false
  try {
    const { data } = await bare.post('/auth/refresh/', { refresh })
    accessToken = data.access
    return true
  } catch {
    clearTokens()
    return false
  }
}

export default client
