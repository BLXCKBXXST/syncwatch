import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getRoom, refreshStream } from '../api/rooms.js'
import { guestLogin } from '../api/auth.js'
import { getAccessToken, refreshAccess } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useRoomSync } from '../hooks/useRoomSync.js'
import RoomSocket from '../ws/roomSocket.js'
import VideoPlayer from '../components/player/VideoPlayer.jsx'
import RoomSidePanel from '../components/room/RoomSidePanel.jsx'
import './WatchRoomPage.css'

// Страница комнаты совместного просмотра: синхронный плеер и боковая панель.
export default function WatchRoomPage() {
  const { roomId } = useParams()
  const { isAuthenticated, loading: authLoading, login } = useAuth()
  const playerRef = useRef(null)
  const [room, setRoom] = useState(null)
  const [error, setError] = useState('')
  const [socket, setSocket] = useState(null)
  const [participants, setParticipants] = useState({ count: 0, viewers: [] })
  const [online, setOnline] = useState(false)
  const [started, setStarted] = useState(false)
  const [copied, setCopied] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  // Зашедшим по ссылке-приглашению без аккаунта автоматически выдаём
  // гостевой — иначе WebSocket подключится как AnonymousUser и не сможет
  // писать в чат/Q&A. Гость живёт 24 часа простоя, потом авто-удаляется.
  useEffect(() => {
    if (authLoading || isAuthenticated) return
    let cancelled = false
    guestLogin()
      .then(({ data }) => {
        if (!cancelled) login(data)
      })
      .catch(() => {
        // Молча: останемся анонимом, форма ввода в чате просто не появится.
      })
    return () => {
      cancelled = true
    }
  }, [authLoading, isAuthenticated, login])

  // Загрузка комнаты по ссылке.
  useEffect(() => {
    let cancelled = false
    getRoom(roomId)
      .then(({ data }) => {
        if (!cancelled) setRoom(data)
      })
      .catch(() => {
        if (!cancelled) setError('Комната не найдена или закрыта.')
      })
    return () => {
      cancelled = true
    }
  }, [roomId])

  // Открытие WebSocket-соединения. Зависит ТОЛЬКО от roomId/isAuthenticated:
  // обработчик room.state ниже обновляет room через setRoom — если бы room
  // входил в deps, любое обновление пересоздавало бы сокет в цикле.
  useEffect(() => {
    if (!roomId) return undefined
    let cancelled = false
    let activeSocket = null
    ;(async () => {
      // Освежаем access-токен, чтобы ведущий не потерял роль из-за истёкшего JWT.
      if (isAuthenticated) await refreshAccess()
      if (cancelled) return
      activeSocket = new RoomSocket(roomId, getAccessToken())
      activeSocket.on('room.participants', (m) =>
        setParticipants({ count: m.count, viewers: m.viewers }),
      )
      // Когда хост передаёт роль или уходит — сервер шлёт обновлённый
      // state с новым host. Синхронизируем локальный признак is_host.
      activeSocket.on('room.state', (m) => {
        if (!m?.host) return
        setRoom((prev) => {
          if (!prev) return prev
          return { ...prev, host: m.host, is_host: m.host.id === getMyUserId() }
        })
      })
      activeSocket.on('socket.status', (m) => setOnline(m.online))
      activeSocket.connect()
      setSocket(activeSocket)
    })()
    return () => {
      cancelled = true
      if (activeSocket) activeSocket.close()
    }
  }, [roomId, isAuthenticated])

  const isHost = Boolean(room?.is_host)
  const { hostHandlers } = useRoomSync({ socket, playerRef, isHost })

  const join = () => {
    setStarted(true)
    playerRef.current?.play()
    socket?.send('player.sync_request')
  }

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const onStreamError = async () => {
    if (!room?.is_external || !isHost || refreshing) return
    setRefreshing(true)
    try {
      const { data } = await refreshStream(roomId)
      setRoom(data)
    } finally {
      setRefreshing(false)
    }
  }

  if (error) return <p className="page-state">{error}</p>
  if (!room) return <p className="page-state">Загрузка комнаты…</p>

  const title = room.display_title || room.video?.title || 'Комната'
  const poster = room.is_external
    ? room.external_thumbnail_url || undefined
    : room.video?.thumbnail_url || undefined
  const streamSrc = room.stream_url || room.video?.stream_url

  return (
    <div className="room">
      <div className="room__main">
        <div className="room__player">
          <VideoPlayer
            ref={playerRef}
            src={streamSrc}
            poster={poster}
            controls={isHost}
            onError={onStreamError}
            {...(hostHandlers || {})}
          />
          {!isHost && !started && (
            <button type="button" className="room__gate" onClick={join}>
              <span className="room__gate-icon">▶</span>
              Присоединиться к просмотру
            </button>
          )}
          {!isHost && started && (
            <div className="room__viewer-badge">Ведущий управляет просмотром</div>
          )}
        </div>
        <h1 className="room__title">{title}</h1>
        <p className="room__sub">
          {isHost
            ? 'Вы ведущий — управляйте плеером, зрители синхронизируются автоматически.'
            : `Ведущий: ${room.host.display_name}`}
          {room.is_external && (
            <>
              {' · '}
              <a href={room.external_url} target="_blank" rel="noreferrer">
                источник
              </a>
            </>
          )}
          {isHost && room.is_external && (
            <>
              {' · '}
              <button
                type="button"
                className="room__refresh"
                onClick={() => onStreamError()}
                disabled={refreshing}
              >
                {refreshing ? 'Обновление…' : 'Обновить поток'}
              </button>
            </>
          )}
        </p>
      </div>

      <RoomSidePanel
        socket={socket}
        roomId={roomId}
        participants={participants}
        online={online}
        canPost={isAuthenticated}
        onCopyLink={copyLink}
        copied={copied}
        isHost={isHost}
      />
    </div>
  )
}

// Идентификатор текущего пользователя из JWT для быстрого сопоставления —
// без вызова /me. Если токена нет, возвращает null (гость, никогда не хост).
function getMyUserId() {
  const token = getAccessToken()
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.user_id ?? null
  } catch {
    return null
  }
}
