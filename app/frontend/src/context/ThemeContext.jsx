import { createContext, useCallback, useContext, useEffect, useState } from 'react'

import { getSiteSettings } from '../api/siteSettings.js'

const ThemeContext = createContext(null)

const THEME_KEY = 'blxckhub:theme'
const ACCENT_KEY = 'blxckhub:accent'
const SERVER_DEFAULT_KEY = 'blxckhub:server-default-theme'

// Свотчи акцента основной тёмной темы. id хранится в localStorage,
// цвета прокидываются в CSS-переменные через inline-стиль на <html>.
export const ACCENTS = [
  { id: 'indigo', label: 'Индиго', color: '#6157ff', hover: '#7a72ff', soft: 'rgba(97, 87, 255, 0.14)' },
  { id: 'teal',   label: 'Бирюза', color: '#22c1c3', hover: '#3fd4d6', soft: 'rgba(34, 193, 195, 0.14)' },
  { id: 'mint',   label: 'Мята',   color: '#3ddc84', hover: '#5be39a', soft: 'rgba(61, 220, 132, 0.14)' },
  { id: 'amber',  label: 'Янтарь', color: '#f5a524', hover: '#f7b748', soft: 'rgba(245, 165, 36, 0.14)' },
  { id: 'ruby',   label: 'Рубин',  color: '#ff5a6a', hover: '#ff7a86', soft: 'rgba(255, 90, 106, 0.14)' },
  { id: 'slate',  label: 'Графит', color: '#8a8a92', hover: '#a0a0a8', soft: 'rgba(138, 138, 146, 0.14)' },
]

const DEFAULT_ACCENT_ID = 'indigo'

const applyTheme = (theme) => {
  document.documentElement.dataset.theme = theme === 'default' ? '' : theme
}

// Провайдер темы интерфейса: переключает скрытые альтернативные темы
// (seans, sonar), акцентный цвет в default и заголовок вкладки.
// При первом заходе пользователя (нет blxckhub:theme в localStorage) —
// подтягивает дефолтную тему из админки через /api/site-settings/.
export function ThemeProvider({ children }) {
  const [hasUserPref] = useState(() => {
    if (typeof window === 'undefined') return false
    return !!window.localStorage.getItem(THEME_KEY)
  })

  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'default'
    const user = window.localStorage.getItem(THEME_KEY)
    if (user) return user
    // Пользователь ещё ничего не выбирал — используем кешированный
    // server-дефолт (его проставляет inline-script в index.html до
    // React-маунта, а useEffect ниже обновляет на каждом монтировании).
    return window.localStorage.getItem(SERVER_DEFAULT_KEY) || 'default'
  })
  const [accent, setAccentState] = useState(() => {
    if (typeof window === 'undefined') return DEFAULT_ACCENT_ID
    const stored = window.localStorage.getItem(ACCENT_KEY)
    return ACCENTS.some((a) => a.id === stored) ? stored : DEFAULT_ACCENT_ID
  })

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  // Под seans/sonar свои акценты в CSS — снимаем override, чтобы каскад
  // из соответствующей темы снова имел силу.
  useEffect(() => {
    const style = document.documentElement.style
    if (theme === 'default') {
      const swatch = ACCENTS.find((a) => a.id === accent) || ACCENTS[0]
      style.setProperty('--color-accent', swatch.color)
      style.setProperty('--color-accent-hover', swatch.hover)
      style.setProperty('--color-accent-soft', swatch.soft)
    } else {
      style.removeProperty('--color-accent')
      style.removeProperty('--color-accent-hover')
      style.removeProperty('--color-accent-soft')
    }
  }, [theme, accent])

  useEffect(() => {
    if (theme === 'seans') document.title = 'СЕАНС'
    else if (theme === 'sonar') document.title = 'Sonar'
    else document.title = 'Syncwatch'
  }, [theme])

  // Серверный дефолт темы — применяется только если у пользователя нет
  // собственного выбора в localStorage. Тихо падает при ошибке сети.
  useEffect(() => {
    if (hasUserPref) return
    let cancelled = false
    getSiteSettings()
      .then(({ default_theme: serverDefault }) => {
        if (cancelled || !serverDefault) return
        window.localStorage.setItem(SERVER_DEFAULT_KEY, serverDefault)
        setTheme((prev) => (prev === serverDefault ? prev : serverDefault))
      })
      .catch(() => { /* молча — остаёмся на текущей теме */ })
    return () => { cancelled = true }
  }, [hasUserPref])

  const toggle = useCallback(() => {
    setTheme((current) => {
      const next = current === 'seans' ? 'default' : 'seans'
      window.localStorage.setItem(THEME_KEY, next)
      return next
    })
  }, [])

  const selectTheme = useCallback((next) => {
    setTheme(() => {
      window.localStorage.setItem(THEME_KEY, next)
      return next
    })
  }, [])

  const setAccent = useCallback((id) => {
    if (!ACCENTS.some((a) => a.id === id)) return
    window.localStorage.setItem(ACCENT_KEY, id)
    setAccentState(id)
  }, [])

  const value = { theme, toggle, selectTheme, accent, setAccent, accents: ACCENTS }

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    throw new Error('useTheme должен использоваться внутри ThemeProvider')
  }
  return ctx
}
