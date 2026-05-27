import { useEffect, useState } from 'react'
import { updateVideo } from '../../api/videos.js'
import Button from '../ui/Button.jsx'
import TextField from '../ui/TextField.jsx'
import './EditVideoModal.css'

// Модалка редактирования метаданных видео: название, описание, публикация.
// Сам файл видео не меняется — это правка только метаданных через PATCH.
export default function EditVideoModal({ video, onClose, onSaved }) {
  const [title, setTitle] = useState(video.title || '')
  const [description, setDescription] = useState(video.description || '')
  const [isPublic, setIsPublic] = useState(Boolean(video.is_public))
  const [thumbnailFile, setThumbnailFile] = useState(null)
  const [thumbnailPreview, setThumbnailPreview] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  // Локальный preview выбранного файла; чистим object URL при уходе.
  useEffect(() => {
    if (!thumbnailFile) {
      setThumbnailPreview(null)
      return undefined
    }
    const url = URL.createObjectURL(thumbnailFile)
    setThumbnailPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [thumbnailFile])

  // Закрытие по Escape.
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  const submit = async (e) => {
    e.preventDefault()
    if (!title.trim()) return
    setSaving(true)
    setError('')
    try {
      let body
      if (thumbnailFile) {
        body = new FormData()
        body.append('title', title.trim())
        body.append('description', description)
        body.append('is_public', isPublic ? 'true' : 'false')
        body.append('thumbnail', thumbnailFile)
      } else {
        body = {
          title: title.trim(),
          description,
          is_public: isPublic,
        }
      }
      const { data } = await updateVideo(video.id, body)
      onSaved(data)
    } catch (err) {
      setError('Не удалось сохранить изменения.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="edit-modal" onMouseDown={onClose}>
      <div className="edit-modal__card" onMouseDown={(e) => e.stopPropagation()}>
        <h2 className="edit-modal__title">Редактирование видео</h2>
        <form onSubmit={submit} className="edit-modal__form">
          <TextField
            label="Название"
            name="title"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <label className="edit-modal__field">
            <span className="edit-modal__label">Описание</span>
            <textarea
              className="edit-modal__textarea"
              rows={5}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>

          <div className="edit-modal__thumb">
            <span className="edit-modal__label">Превью</span>
            <div className="edit-modal__thumb-row">
              {(thumbnailPreview || video.thumbnail_url) ? (
                <img
                  className="edit-modal__thumb-preview"
                  src={thumbnailPreview || video.thumbnail_url}
                  alt=""
                />
              ) : (
                <div className="edit-modal__thumb-preview edit-modal__thumb-preview--empty">
                  ▶
                </div>
              )}
              <div className="edit-modal__thumb-controls">
                <label className="edit-modal__file-btn">
                  Выбрать файл
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setThumbnailFile(e.target.files?.[0] || null)}
                  />
                </label>
                {thumbnailFile && (
                  <button
                    type="button"
                    className="edit-modal__file-clear"
                    onClick={() => setThumbnailFile(null)}
                  >
                    Сбросить выбор
                  </button>
                )}
                <span className="edit-modal__file-name">
                  {thumbnailFile ? thumbnailFile.name : 'не изменено'}
                </span>
              </div>
            </div>
          </div>

          <label className="edit-modal__check">
            <input
              type="checkbox"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
            />
            <span>Видео публичное (отображается в общей ленте)</span>
          </label>

          {error && <p className="edit-modal__error">{error}</p>}

          <div className="edit-modal__actions">
            <Button type="submit" loading={saving} disabled={!title.trim()}>
              Сохранить
            </Button>
            <Button type="button" variant="ghost" onClick={onClose}>
              Отмена
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
