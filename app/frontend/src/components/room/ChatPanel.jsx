import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMessages } from '../../api/chat.js'
import MessageCard from '../ui/MessageCard.jsx'
import Button from '../ui/Button.jsx'

// Вкладка живого чата комнаты: история + входящие события + отправка.
export default function ChatPanel({ socket, roomId, canChat }) {
  const [messages, setMessages] = useState([])
  const [liked, setLiked] = useState(() => new Set())
  const [text, setText] = useState('')
  const listRef = useRef(null)

  // История чата при входе в комнату.
  useEffect(() => {
    getMessages(roomId)
      .then(({ data }) => {
        setMessages(data)
        setLiked(new Set(data.filter((m) => m.liked_by_me).map((m) => m.id)))
      })
      .catch(() => {})
  }, [roomId])

  // Живые события чата по WebSocket.
  useEffect(() => {
    if (!socket) return undefined
    const offMessage = socket.on('chat.message', (event) => {
      setMessages((prev) => [...prev, event.message])
    })
    const offLike = socket.on('chat.like', (event) => {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === event.message_id ? { ...m, likes_count: event.likes_count } : m,
        ),
      )
    })
    return () => {
      offMessage()
      offLike()
    }
  }, [socket])

  // Автопрокрутка к свежему сообщению.
  useEffect(() => {
    const el = listRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages])

  const send = (e) => {
    e.preventDefault()
    const value = text.trim()
    if (!value || !socket) return
    socket.send('chat.message', { text: value })
    setText('')
  }

  const toggleLike = (id) => {
    if (!socket || !canChat) return
    socket.send('chat.like', { message_id: id })
    setLiked((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <div className="rpanel">
      <div className="rpanel__list" ref={listRef}>
        {messages.length === 0 && (
          <p className="rpanel__empty">Сообщений пока нет — напишите первое.</p>
        )}
        {messages.map((m) => (
          <MessageCard
            key={m.id}
            message={m}
            liked={liked.has(m.id)}
            onLike={() => toggleLike(m.id)}
          />
        ))}
      </div>

      {canChat ? (
        <form className="rpanel__composer" onSubmit={send}>
          <input
            className="rpanel__input"
            placeholder="Текст"
            value={text}
            maxLength={2000}
            onChange={(e) => setText(e.target.value)}
          />
          <Button type="submit" fullWidth disabled={!text.trim()}>
            Отправить
          </Button>
        </form>
      ) : (
        <Link to="/login" className="rpanel__guest">
          Хотите отправить сообщение? Войдите в аккаунт
        </Link>
      )}
    </div>
  )
}
