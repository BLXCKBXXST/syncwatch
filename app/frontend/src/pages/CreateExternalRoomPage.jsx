import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { createRoom } from '../api/rooms.js'
import { extractError, extractFieldErrors } from '../api/errors.js'
import TextField from '../components/ui/TextField.jsx'
import Button from '../components/ui/Button.jsx'
import './CreateExternalRoomPage.css'

// Создание комнаты совместного просмотра по ссылке на видео. Бэкенд через
// yt-dlp извлекает прямой поток; YouTube не поддерживается (заблокирован
// на стороне валидатора).
export default function CreateExternalRoomPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const presetTitle = searchParams.get('title') || ''
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState(presetTitle)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    setTitle(presetTitle)
  }, [presetTitle])

  const submit = async (e) => {
    e.preventDefault()
    setErrors({})
    setFormError('')
    if (!url.trim()) {
      setErrors({ external_url: 'Укажите ссылку на страницу с видео.' })
      return
    }
    setSubmitting(true)
    try {
      const { data } = await createRoom({
        external_url: url.trim(),
        title: title.trim(),
      })
      navigate(`/room/${data.id}`)
    } catch (err) {
      setErrors(extractFieldErrors(err))
      setFormError(extractError(err, 'Не удалось создать комнату.'))
      setSubmitting(false)
    }
  }

  return (
    <div className="ext-room">
      <h1 className="page-title">Сеанс по ссылке</h1>
      <p className="ext-room__hint">
        Вставьте ссылку на страницу с видео — RuTube, VK Video, Twitch VOD,
        Dailymotion или прямую mp4/m3u8-ссылку. Сервер сам извлечёт поток,
        а участники комнаты будут смотреть синхронно с ведущим.
      </p>
      <p className="ext-room__note">YouTube не поддерживается.</p>
      <form className="ext-room__form" onSubmit={submit} noValidate>
        <TextField
          label="Ссылка на страницу или видео"
          name="external_url"
          type="url"
          placeholder="https://rutube.ru/video/… или прямая mp4/m3u8"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          error={errors.external_url}
          required
        />
        <TextField
          label="Название комнаты (необязательно)"
          name="title"
          placeholder="Подставится из заголовка ролика"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          error={errors.title}
        />
        {formError && <p className="form-error">{formError}</p>}
        <Button type="submit" loading={submitting}>
          {submitting ? 'Создаём…' : 'Создать комнату'}
        </Button>
      </form>
    </div>
  )
}
