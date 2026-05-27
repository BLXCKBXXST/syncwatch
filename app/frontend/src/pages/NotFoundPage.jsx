import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="page-state">
      <h1 style={{ fontSize: 56 }}>404</h1>
      <p>
        Страница не найдена. <Link to="/">Вернуться в ленту</Link>.
      </p>
    </div>
  )
}
