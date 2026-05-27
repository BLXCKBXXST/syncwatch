import { useEffect, useId, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadVideo } from '../api/videos.js'
import { extractError, extractFieldErrors } from '../api/errors.js'
import TextField from '../components/ui/TextField.jsx'
import Button from '../components/ui/Button.jsx'
import './UploadPage.css'

// Поле выбора файла с показом имени выбранного файла.
function FilePicker({ label, accept, file, onPick, error, required }) {
  const id = useId()
  return (
    <div className={`field${error ? ' field--error' : ''}`}>
      <span className="field__label">{label}</span>
      <label className="filepicker" htmlFor={id}>
        <span className="filepicker__btn">Выбрать файл</span>
        <span className="filepicker__name">{file ? file.name : 'Файл не выбран'}</span>
        <input
          id={id}
          type="file"
          accept={accept}
          required={required}
          onChange={(e) => onPick(e.target.files[0] || null)}
        />
      </label>
      {error && <p className="field__error">{error}</p>}
    </div>
  )
}

// Страница загрузки нового видео.
export default function UploadPage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState(null)
  const [thumbnail, setThumbnail] = useState(null)
  const [thumbnailPreview, setThumbnailPreview] = useState(null)
  const [isPublic, setIsPublic] = useState(true)

  // Локальный preview выбранного превью; чистим object URL при уходе.
  useEffect(() => {
    if (!thumbnail) {
      setThumbnailPreview(null)
      return undefined
    }
    const url = URL.createObjectURL(thumbnail)
    setThumbnailPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [thumbnail])
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [progress, setProgress] = useState(0)
  const [uploading, setUploading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setErrors({})
    setFormError('')
    if (!file) {
      setErrors({ file: 'Выберите видеофайл.' })
      return
    }

    const data = new FormData()
    data.append('title', title)
    data.append('description', description)
    data.append('file', file)
    if (thumbnail) data.append('thumbnail', thumbnail)
    data.append('is_public', isPublic ? 'true' : 'false')

    setUploading(true)
    try {
      const resp = await uploadVideo(data, (event) => {
        if (event.total) {
          setProgress(Math.round((event.loaded / event.total) * 100))
        }
      })
      navigate(`/video/${resp.data.id}`)
    } catch (err) {
      setErrors(extractFieldErrors(err))
      setFormError(extractError(err, 'Не удалось загрузить видео.'))
      setUploading(false)
    }
  }

  return (
    <div className="upload">
      <h1 className="page-title">Загрузка видео</h1>
      <form className="upload__form" onSubmit={submit} noValidate>
        <TextField
          label="Название"
          name="title"
          placeholder="Название ролика"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          error={errors.title}
          required
        />

        <div className="field">
          <label className="field__label" htmlFor="upload-descr">
            Описание
          </label>
          <textarea
            id="upload-descr"
            className="field__input upload__textarea"
            rows={4}
            placeholder="О чём это видео"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        <FilePicker
          label="Видеофайл"
          accept="video/*"
          file={file}
          onPick={setFile}
          error={errors.file}
          required
        />
        <FilePicker
          label="Превью (необязательно)"
          accept="image/*"
          file={thumbnail}
          onPick={setThumbnail}
          error={errors.thumbnail}
        />
        {thumbnailPreview && (
          <img className="upload__thumb-preview" src={thumbnailPreview} alt="" />
        )}

        <label className="upload__check">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
          />
          Опубликовать в общей ленте
        </label>

        {uploading && progress > 0 && (
          <div className="upload__progress">
            <div className="upload__progress-bar" style={{ width: `${progress}%` }} />
          </div>
        )}

        {formError && <p className="form-error">{formError}</p>}

        <Button type="submit" loading={uploading}>
          {uploading ? `Загрузка… ${progress}%` : 'Загрузить'}
        </Button>
      </form>
    </div>
  )
}
