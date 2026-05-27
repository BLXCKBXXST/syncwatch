import { useEffect, useRef, useState } from 'react'
import { useTheme } from '../context/ThemeContext.jsx'
import './ThemeMenu.css'

// Скрытое меню переключателя темы и акцента. Триггер — крохотный кружок,
// едва заметный на фоне профиля. По клику разворачивается всплывающая
// карточка; закрывается по клику вне, Escape или повторному клику.
export default function ThemeMenu() {
  const { theme, selectTheme, accent, setAccent, accents } = useTheme()
  const [open, setOpen] = useState(false)
  const wrapperRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    const onKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClickOutside)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <span className="theme-menu" ref={wrapperRef}>
      <button
        type="button"
        className="theme-menu__trigger"
        aria-label=""
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        ●
      </button>
      {open && (
        <div className="theme-menu__pop" role="menu">
          <div className="theme-menu__section">
            <div className="theme-menu__title">Тема</div>
            <button
              type="button"
              className={
                'theme-menu__item' +
                (theme === 'default' ? ' theme-menu__item--active' : '')
              }
              onClick={() => selectTheme('default')}
            >
              <span className="theme-menu__dot theme-menu__dot--default" />
              blxck.hub
            </button>
            <button
              type="button"
              className={
                'theme-menu__item' +
                (theme === 'seans' ? ' theme-menu__item--active' : '')
              }
              onClick={() => selectTheme('seans')}
            >
              <span className="theme-menu__dot theme-menu__dot--seans" />
              СЕАНС
            </button>
            <button
              type="button"
              className={
                'theme-menu__item' +
                (theme === 'sonar' ? ' theme-menu__item--active' : '')
              }
              onClick={() => selectTheme('sonar')}
            >
              <span className="theme-menu__dot theme-menu__dot--sonar" />
              Sonar
            </button>
          </div>

          {theme === 'default' && (
            <div className="theme-menu__section">
              <div className="theme-menu__title">Акцент</div>
              <div className="theme-menu__swatches">
                {accents.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    className={
                      'theme-menu__swatch' +
                      (accent === s.id ? ' theme-menu__swatch--active' : '')
                    }
                    style={{ background: s.color }}
                    aria-label={s.label}
                    onClick={() => setAccent(s.id)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </span>
  )
}
