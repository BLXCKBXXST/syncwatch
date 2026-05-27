import client from './client.js'

// Глобальные настройки сайта (дефолтная тема для новых пользователей).
export async function getSiteSettings() {
  const { data } = await client.get('/site-settings/')
  return data
}
