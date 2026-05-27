import { Outlet } from 'react-router-dom'
import Header from './Header.jsx'
import './Layout.css'

// Каркас страниц с шапкой (всё, кроме экранов авторизации).
export default function Layout() {
  return (
    <div className="layout">
      <Header />
      <main className="layout__main">
        <Outlet />
      </main>
    </div>
  )
}
