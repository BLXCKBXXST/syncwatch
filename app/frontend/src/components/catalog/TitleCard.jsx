import { Link } from 'react-router-dom'
import './TitleCard.css'

// Карточка фильма/сериала в ленте каталога.
export default function TitleCard({ source, title }) {
  const yearSuffix = title.year ? ` (${title.year})` : ''
  return (
    <Link to={`/catalog/${source}/${title.id}`} className="title-card">
      <div className="title-card__poster">
        {title.poster ? (
          <img src={title.poster} alt={title.title} loading="lazy" />
        ) : (
          <div className="title-card__poster-empty">{title.title.slice(0, 1)}</div>
        )}
        {title.rating ? (
          <span className="title-card__rating">{title.rating.toFixed(1)}</span>
        ) : null}
        {title.kind === 'series' && <span className="title-card__badge">сериал</span>}
      </div>
      <div className="title-card__title">
        {title.title}
        <span className="title-card__year">{yearSuffix}</span>
      </div>
    </Link>
  )
}
