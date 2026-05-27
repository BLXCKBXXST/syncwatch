import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { fetchTitle } from '../api/catalog.js'
import { extractError } from '../api/errors.js'
import Button from '../components/ui/Button.jsx'
import './CatalogTitlePage.css'

// Страница тайтла каталога: метаданные TMDB + действия. Потоков нет —
// зритель копирует название и создаёт «Сеанс по ссылке» с любого
// доступного источника (RuTube, VK Video, Twitch и т.д.).
export default function CatalogTitlePage() {
  const { source, externalId } = useParams()
  const navigate = useNavigate()
  const [details, setDetails] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [season, setSeason] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetchTitle(source, externalId)
      .then(({ data }) => {
        if (cancelled) return
        setDetails(data)
        if (data.seasons?.length) {
          setSeason(data.seasons[0].number)
        }
      })
      .catch((err) =>
        !cancelled && setError(extractError(err, 'Не удалось загрузить страницу тайтла.')),
      )
    return () => {
      cancelled = true
    }
  }, [source, externalId])

  if (error) return <p className="page-state">{error}</p>
  if (!details) return <p className="page-state">Загрузка…</p>

  const titleWithYear = details.year
    ? `${details.title} (${details.year})`
    : details.title

  const copyTitle = async () => {
    try {
      await navigator.clipboard.writeText(titleWithYear)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard может быть недоступен */
    }
  }

  const startSession = () => {
    navigate(`/rooms/new?title=${encodeURIComponent(titleWithYear)}`)
  }

  const selectedSeason = details.seasons?.find((s) => s.number === season)

  return (
    <div className="catalog-title">
      <div className="catalog-title__head">
        <div className="catalog-title__poster">
          {details.poster ? (
            <img src={details.poster} alt={details.title} />
          ) : (
            <div className="catalog-title__poster-empty">
              {details.title.slice(0, 1)}
            </div>
          )}
        </div>
        <div className="catalog-title__info">
          <h1 className="catalog-title__name">
            {details.title}
            {details.year ? (
              <span className="catalog-title__year"> ({details.year})</span>
            ) : null}
          </h1>

          <div className="catalog-title__meta">
            {details.kind === 'series' && <span>Сериал</span>}
            {details.rating ? <span>★ {details.rating.toFixed(1)}</span> : null}
            {details.duration_minutes ? (
              <span>{details.duration_minutes} мин</span>
            ) : null}
            {details.genres?.length > 0 && <span>{details.genres.join(', ')}</span>}
          </div>

          {details.description && (
            <p className="catalog-title__descr">{details.description}</p>
          )}

          <div className="catalog-title__actions">
            <Button onClick={copyTitle}>
              {copied ? 'Скопировано' : 'Скопировать название'}
            </Button>
            <Button variant="secondary" onClick={startSession}>
              Создать сеанс по ссылке
            </Button>
            {details.url && (
              <a
                className="catalog-title__source"
                href={details.url}
                target="_blank"
                rel="noreferrer"
              >
                Открыть в источнике
              </a>
            )}
          </div>
        </div>
      </div>

      {details.seasons?.length > 0 && (
        <div className="catalog-title__seasons">
          <h2 className="catalog-title__subtitle">Сезоны</h2>
          <div className="catalog-title__seasons-tabs">
            {details.seasons.map((s) => (
              <button
                key={s.number}
                type="button"
                className={
                  'catalog-title__season-tab' +
                  (s.number === season ? ' catalog-title__season-tab--active' : '')
                }
                onClick={() => setSeason(s.number)}
              >
                Сезон {s.number}
              </button>
            ))}
          </div>
          {selectedSeason && (
            <ol className="catalog-title__episodes">
              {selectedSeason.episodes.map((ep) => (
                <li key={ep.number}>
                  <span className="catalog-title__ep-num">{ep.number}.</span>{' '}
                  {ep.title || 'Без названия'}
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
    </div>
  )
}
