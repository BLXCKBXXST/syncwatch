import { NavLink } from 'react-router-dom'
import { useTheme } from '../../context/ThemeContext.jsx'
import './AuthLayout.css'

const tabClass = ({ isActive }) =>
  isActive ? 'auth__tab auth__tab--active' : 'auth__tab'

// Общий каркас экранов авторизации: фон, логотип, вкладки и карточка с формой.
export default function AuthLayout({ children }) {
  const { theme } = useTheme()
  return (
    <div className="auth">
      <div className="auth__backdrop" aria-hidden="true" />
      <div className="auth__inner">
        <div className="auth__brand">
          {theme === 'seans' ? (
            <>СЕ<span>АНС</span></>
          ) : theme === 'sonar' ? (
            <>
              <svg className="brand-echo" viewBox="0 0 14 14" aria-hidden="true">
                <circle cx="7" cy="7" r="1.5" fill="currentColor" />
                <circle cx="7" cy="7" r="4" fill="none" stroke="currentColor" strokeWidth="1.2" opacity="0.5" />
                <circle cx="7" cy="7" r="6.3" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.25" />
              </svg>
              Sonar
            </>
          ) : (
            <>blxck<span>.hub</span></>
          )}
        </div>
        <nav className="auth__tabs">
          <NavLink to="/register" className={tabClass}>
            Регистрация
          </NavLink>
          <NavLink to="/login" className={tabClass}>
            Вход
          </NavLink>
        </nav>
        <div className="auth__card">{children}</div>
      </div>
    </div>
  )
}
