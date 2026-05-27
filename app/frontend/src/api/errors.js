// Извлечение человекочитаемых сообщений из ответов DRF об ошибках.

export function extractError(err, fallback = 'Что-то пошло не так. Попробуйте ещё раз.') {
  const data = err?.response?.data
  if (!data) return err?.message || fallback
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  const first = Object.values(data)[0]
  if (Array.isArray(first)) return first[0]
  if (typeof first === 'string') return first
  return fallback
}

// Преобразует ответ DRF в карту { имя_поля: сообщение } для подсветки полей формы.
export function extractFieldErrors(err) {
  const data = err?.response?.data
  const result = {}
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    for (const [key, value] of Object.entries(data)) {
      result[key] = Array.isArray(value) ? value[0] : String(value)
    }
  }
  return result
}
