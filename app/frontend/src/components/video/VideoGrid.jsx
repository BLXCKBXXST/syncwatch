import VideoCard from './VideoCard.jsx'
import './VideoGrid.css'

// Сетка видеокарточек. renderActions — необязательный рендер кнопок под карточкой
// (используется на странице профиля для правки и удаления).
export default function VideoGrid({ videos, renderActions }) {
  return (
    <div className="vgrid">
      {videos.map((video) => (
        <div key={video.id} className="vgrid__item">
          <VideoCard video={video} />
          {renderActions && <div className="vgrid__actions">{renderActions(video)}</div>}
        </div>
      ))}
    </div>
  )
}
