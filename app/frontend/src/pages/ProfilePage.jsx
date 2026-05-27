import { useEffect, useState } from 'react'
import { deleteVideo, myVideos } from '../api/videos.js'
import { updateMe } from '../api/auth.js'
import { useAuth } from '../context/AuthContext.jsx'
import VideoGrid from '../components/video/VideoGrid.jsx'
import Button from '../components/ui/Button.jsx'
import TextField from '../components/ui/TextField.jsx'
import ThemeMenu from '../components/ThemeMenu.jsx'
import './ProfilePage.css'

// Профиль пользователя: данные, имя в чате и управление своими видео.
export default function ProfilePage() {
  const { user, isGuest, updateUser } = useAuth()
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingName, setEditingName] = useState(false)
  const [chatName, setChatName] = useState(user.chat_display_name || '')
  const [savingName, setSavingName] = useState(false)

  useEffect(() => {
    let cancelled = false
    myVideos()
      .then(({ data }) => {
        if (!cancelled) setVideos(data.results)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const remove = async (video) => {
    if (!window.confirm(`Удалить видео «${video.title}»?`)) return
    await deleteVideo(video.id)
    setVideos((list) => list.filter((item) => item.id !== video.id))
  }

  const saveName = async () => {
    setSavingName(true)
    try {
      const { data } = await updateMe({ chat_display_name: chatName })
      updateUser(data)
      setEditingName(false)
    } finally {
      setSavingName(false)
    }
  }

  return (
    <div className="profile">
      <div className="profile__head">
        <div className="profile__avatar">
          {user.display_name.slice(0, 1).toUpperCase()}
        </div>
        <div>
          <h1 className="profile__name">{user.display_name}</h1>
          <p className="profile__email">
            @{user.username}
            <ThemeMenu />
          </p>
        </div>
      </div>

      {isGuest && (
        <p className="profile__guest-note">
          Это гостевой аккаунт. Он будет удалён после 24 часов простоя вместе
          со всеми загруженными видео и комнатами. Зарегистрируйтесь, чтобы
          сохранить доступ.
        </p>
      )}

      <div className="profile__chatname">
        {editingName ? (
          <>
            <TextField
              label="Имя в чате"
              name="chatName"
              placeholder="Как вас видно в комнатах просмотра"
              value={chatName}
              onChange={(e) => setChatName(e.target.value)}
            />
            <div className="profile__chatname-actions">
              <Button onClick={saveName} loading={savingName}>
                Сохранить
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setEditingName(false)
                  setChatName(user.chat_display_name || '')
                }}
              >
                Отмена
              </Button>
            </div>
          </>
        ) : (
          <p>
            Имя в чате: <b>{user.display_name}</b>
            <button
              type="button"
              className="profile__edit-link"
              onClick={() => setEditingName(true)}
            >
              Ред.
            </button>
          </p>
        )}
      </div>

      <h2 className="profile__subtitle">Мои видео</h2>
      {loading && <p className="page-state">Загрузка…</p>}
      {!loading && videos.length === 0 && (
        <p className="page-state">Вы ещё не загрузили ни одного видео.</p>
      )}
      {videos.length > 0 && (
        <VideoGrid
          videos={videos}
          renderActions={(video) => (
            <Button variant="danger" onClick={() => remove(video)}>
              Удалить
            </Button>
          )}
        />
      )}
    </div>
  )
}
