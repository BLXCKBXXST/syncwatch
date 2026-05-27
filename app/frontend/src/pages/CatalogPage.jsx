import { useCallback, useEffect, useState } from 'react'
import { fetchFeed, searchCatalog } from '../api/catalog.js'
import { extractError } from '../api/errors.js'
import TitleCard from '../components/catalog/TitleCard.jsx'
import Button from '../components/ui/Button.jsx'
import TextField from '../components/ui/TextField.jsx'
import './CatalogPage.css'

const SOURCE = 'kinopoiskdev'

// Каталог-справочник: метаданные о фильмах и сериалах через poiskkino.dev.
// Сами потоки не отдаются — пользователь копирует название и открывает
// «Сеанс по ссылке» с нужным URL.
export default function CatalogPage() {
  const [items, setItems] = useState([])
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [kind, setKind] = useState('movie') // 'movie' | 'series'

  const load = useCallback(
    async (nextPage, q, k) => {
      setLoading(true)
      setError('')
      try {
        const req = q
          ? searchCatalog(SOURCE, q, nextPage)
          : fetchFeed(SOURCE, { page: nextPage, kind: k })
        const { data } = await req
        setItems((prev) => (nextPage === 1 ? data.items : [...prev, ...data.items]))
        setHasNext(Boolean(data.has_next))
        setPage(nextPage)
      } catch (err) {
        setError(
          extractError(
            err,
            'Каталог временно недоступен. Возможно, не настроен токен в админке (получить — у @poiskkinodev_bot в Telegram).',
          ),
        )
        if (nextPage === 1) setItems([])
        setHasNext(false)
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  useEffect(() => {
    load(1, submittedQuery, kind)
  }, [submittedQuery, kind, load])

  const submitSearch = (e) => {
    e.preventDefault()
    setSubmittedQuery(query.trim())
  }

  const resetSearch = () => {
    setQuery('')
    setSubmittedQuery('')
  }

  return (
    <div className="catalog">
      <h1 className="page-title">Каталог</h1>
      <p className="catalog__hint">
        Справочник фильмов и сериалов. Выберите тайтл, скопируйте название —
        и создайте «Сеанс по ссылке» с нужного источника.
      </p>

      {!submittedQuery && (
        <div className="catalog__chips">
          <button
            type="button"
            className={
              'catalog__chip' + (kind === 'movie' ? ' catalog__chip--active' : '')
            }
            onClick={() => setKind('movie')}
          >
            Фильмы
          </button>
          <button
            type="button"
            className={
              'catalog__chip' + (kind === 'series' ? ' catalog__chip--active' : '')
            }
            onClick={() => setKind('series')}
          >
            Сериалы
          </button>
        </div>
      )}

      <form className="catalog__search" onSubmit={submitSearch}>
        <TextField
          name="q"
          placeholder="Поиск фильмов и сериалов"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" disabled={loading}>Найти</Button>
        {submittedQuery && (
          <Button type="button" variant="ghost" onClick={resetSearch}>
            Сбросить
          </Button>
        )}
      </form>

      {error && <p className="form-error">{error}</p>}

      {items.length === 0 && !loading && !error && (
        <p className="page-state">Ничего не найдено.</p>
      )}

      <div className="catalog__grid">
        {items.map((t) => (
          <TitleCard key={t.id} source={SOURCE} title={t} />
        ))}
      </div>

      {hasNext && (
        <div className="catalog__more">
          <Button
            variant="secondary"
            onClick={() => load(page + 1, submittedQuery, kind)}
            loading={loading}
          >
            Показать ещё
          </Button>
        </div>
      )}
      {loading && items.length === 0 && (
        <p className="page-state">Загрузка…</p>
      )}
    </div>
  )
}
