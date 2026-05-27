import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { useTheme } from '../context/ThemeContext.jsx'
import Button from './ui/Button.jsx'
import './Header.css'

// Шапка приложения: логотип, кнопка загрузки, профиль и выход.
export default function Header() {
  const { user, isAuthenticated, isGuest, logout } = useAuth()
  const { theme } = useTheme()

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/" className="header__brand">
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
        </Link>

        <nav className="header__nav">
          {isAuthenticated ? (
            <>
              <Link to="/catalog">
                <Button variant="ghost">Каталог</Button>
              </Link>
              <Link to="/rooms/new">
                <Button variant="ghost">Сеанс по ссылке</Button>
              </Link>
              <Link to="/upload">
                <Button variant="secondary">Загрузить видео</Button>
              </Link>
              {isGuest && (
                <span
                  className="header__guest"
                  title="Гостевой аккаунт удаляется после 24 часов простоя"
                >
                  гость
                </span>
              )}
              <Link to="/profile" className="header__user" title="Профиль">
                <span className="header__avatar">
                  {user.display_name.slice(0, 1).toUpperCase()}
                </span>
                <span className="header__user-name">{user.display_name}</span>
              </Link>
              <Button variant="ghost" onClick={logout}>
                Выйти
              </Button>
            </>
          ) : (
            <Link to="/login">
              <Button>Войти</Button>
            </Link>
          )}
        </nav>
      </div>
    </header>
  )
}
