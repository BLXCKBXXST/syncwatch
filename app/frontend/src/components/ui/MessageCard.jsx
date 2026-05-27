import './MessageCard.css'

// Карточка сообщения чата по макету Figma: автор, текст и лайк со счётчиком.
export default function MessageCard({ message, liked, onLike }) {
  return (
    <div className="msg">
      <div className="msg__body">
        <span className="msg__author">{message.display_name}</span>
        <p className="msg__text">{message.text}</p>
      </div>
      <button
        type="button"
        className={`msg__like${liked ? ' msg__like--on' : ''}`}
        onClick={onLike}
        aria-label="Нравится"
        aria-pressed={liked}
      >
        <span className="msg__heart">♥</span>
        <span className="msg__count">{message.likes_count}</span>
      </button>
    </div>
  )
}
