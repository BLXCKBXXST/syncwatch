// Форматирование значений для интерфейса.

export function formatDuration(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds || 0))
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  const pad = (n) => String(n).padStart(2, '0')
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`
}

export function formatViews(count) {
  const n = count || 0
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} млн`
  if (n >= 1000) return `${(n / 1000).toFixed(1)} тыс.`
  return String(n)
}

export function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}
