import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listVideos } from '../api/videos.js'
import { useAuth } from '../context/AuthContext.jsx'
import VideoGrid from '../components/video/VideoGrid.jsx'
import Button from '../components/ui/Button.jsx'

// Главная страница — лента опубликованных видео с подгрузкой по страницам.
export default function HomePage() {
  const { isAuthenticated } = useAuth()
  const [videos, setVideos] = useState([])
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState('')

  // Первая страница ленты при открытии.
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const { data } = await listVideos({ page: 1 })
        if (cancelled) return
        setVideos(data.results)
        setHasMore(Boolean(data.next))
      } catch {
        if (!cancelled) setError('Не удалось загрузить ленту видео.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  // Подгрузка следующих страниц по кнопке.
  const loadMore = async () => {
    setLoadingMore(true)
    try {
      const next = page + 1
      const { data } = await listVideos({ page: next })
      setVideos((prev) => [...prev, ...data.results])
      setHasMore(Boolean(data.next))
      setPage(next)
    } catch {
      setError('Не удалось загрузить ленту видео.')
    } finally {
      setLoadingMore(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">Лента видео</h1>

      {error && <p className="page-state">{error}</p>}

      {!error && !loading && videos.length === 0 && (
        <p className="page-state">
          Пока нет ни одного видео.{' '}
          {isAuthenticated ? (
            <Link to="/upload">Загрузите первое</Link>
          ) : (
            <Link to="/register">Зарегистрируйтесь и загрузите первое</Link>
          )}
          .
        </p>
      )}

      {loading && <p className="page-state">Загрузка…</p>}

      {videos.length > 0 && <VideoGrid videos={videos} />}

      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: 'var(--space-6)' }}>
          <Button variant="secondary" loading={loadingMore} onClick={loadMore}>
            Показать ещё
          </Button>
        </div>
      )}
    </div>
  )
}
