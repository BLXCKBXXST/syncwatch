import client from './client.js'

// REST-клиент к catalog-приложению бэкенда. Все эндпоинты открыты (AllowAny).
export const listSources = () => client.get('/catalog/sources/')
export const fetchFeed = (source, { page = 1, kind } = {}) => {
  const params = { page }
  if (kind) params.kind = kind
  return client.get(`/catalog/${source}/feed/`, { params })
}
export const searchCatalog = (source, query, page = 1) =>
  client.get(`/catalog/${source}/search/`, { params: { q: query, page } })
export const fetchTitle = (source, externalId) =>
  client.get(`/catalog/${source}/title/${externalId}/`)
export const fetchStream = (source, externalId, { season, episode } = {}) => {
  const params = {}
  if (season) params.s = season
  if (episode) params.e = episode
  return client.get(`/catalog/${source}/stream/${externalId}/`, { params })
}
