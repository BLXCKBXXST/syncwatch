import { Link } from 'react-router-dom'
import { formatDuration, formatViews } from '../../lib/format.js'
import './VideoCard.css'

// Карточка видео для ленты и профиля.
export default function VideoCard({ video }) {
  return (
    <Link to={`/video/${video.id}`} className="vcard">
      <div className="vcard__thumb">
        {video.thumbnail_url ? (
          <img src={video.thumbnail_url} alt="" loading="lazy" />
        ) : (
          <div className="vcard__thumb-fallback" aria-hidden="true">
            ▶
          </div>
        )}
        {video.duration_seconds > 0 && (
          <span className="vcard__duration">
            {formatDuration(video.duration_seconds)}
          </span>
        )}
      </div>
      <div className="vcard__body">
        <h3 className="vcard__title">{video.title}</h3>
        <p className="vcard__meta">
          {video.owner.display_name} · {formatViews(video.views_count)} просмотров
        </p>
      </div>
    </Link>
  )
}
