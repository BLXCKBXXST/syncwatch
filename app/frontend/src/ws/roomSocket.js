// WebSocket-клиент комнаты совместного просмотра.
// Подписка по типу сообщения, автопереподключение с возрастающей паузой.

export default class RoomSocket {
  constructor(roomId, token) {
    this.roomId = roomId
    this.token = token
    this.handlers = {}
    this.ws = null
    this.closed = false
    this.reconnectDelay = 1000
  }

  connect() {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const base = import.meta.env.VITE_WS_BASE || `${proto}://${window.location.host}`
    const query = this.token ? `?token=${this.token}` : ''
    this.ws = new WebSocket(`${base}/ws/rooms/${this.roomId}/${query}`)

    this.ws.onopen = () => {
      this.reconnectDelay = 1000
      this._emit('socket.status', { online: true })
    }
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      this._emit(message.type, message)
    }
    this.ws.onclose = () => {
      this._emit('socket.status', { online: false })
      if (this.closed) return
      // Переподключение с увеличивающейся задержкой (не дольше 10 с).
      setTimeout(() => this.connect(), this.reconnectDelay)
      this.reconnectDelay = Math.min(this.reconnectDelay * 1.6, 10000)
    }
  }

  // Подписка на сообщение определённого типа. Возвращает функцию отписки.
  on(type, handler) {
    if (!this.handlers[type]) this.handlers[type] = []
    this.handlers[type].push(handler)
    return () => {
      this.handlers[type] = this.handlers[type].filter((h) => h !== handler)
    }
  }

  _emit(type, payload) {
    ;(this.handlers[type] || []).forEach((handler) => handler(payload))
  }

  send(type, payload = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, ...payload }))
    }
  }

  close() {
    this.closed = true
    if (this.ws) this.ws.close()
  }
}
