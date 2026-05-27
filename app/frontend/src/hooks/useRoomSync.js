import { useEffect, useRef } from 'react'
import { expectedPosition, syncDecision } from '../lib/sync.js'

const SYNC_INTERVAL_MS = 3000

// Хук синхронизации плеера с состоянием комнаты.
// Ведущий рассылает свои действия; зритель применяет состояние и корректирует
// дрейф. Возвращает обработчики событий плеера для ведущего.
export function useRoomSync({ socket, playerRef, isHost }) {
  // Последний снимок состояния комнаты: { position, isPlaying, clientTime }.
  const baseRef = useRef(null)

  // Применение приходящего состояния комнаты к плееру зрителя.
  useEffect(() => {
    if (!socket) return undefined
    const off = socket.on('room.state', (msg) => {
      baseRef.current = {
        position: msg.position,
        isPlaying: msg.is_playing,
        clientTime: Date.now() / 1000,
      }
      if (isHost) return // ведущий — источник правды, себя не двигаем
      const player = playerRef.current
      if (!player) return
      if (Math.abs(player.getTime() - msg.position) > 0.3) {
        player.seek(msg.position)
      }
      if (msg.is_playing) player.play()
      else player.pause()
    })
    socket.send('player.sync_request')
    return off
  }, [socket, isHost, playerRef])

  // Периодическая коррекция дрейфа у зрителя.
  useEffect(() => {
    if (isHost || !socket) return undefined
    const player = playerRef.current
    const timer = setInterval(() => {
      const base = baseRef.current
      if (!base || !player || !base.isPlaying) return
      const expected = expectedPosition(base, Date.now() / 1000)
      const decision = syncDecision(player.getTime() - expected)
      if (decision.action === 'seek') player.seek(expected)
      player.setPlaybackRate(decision.rate)
    }, SYNC_INTERVAL_MS)
    return () => {
      clearInterval(timer)
      if (player) player.setPlaybackRate(1)
    }
  }, [socket, isHost, playerRef])

  // Команды ведущего уходят на сервер вместе с фактическим состоянием плеера.
  const sendHostAction = (type) => {
    const player = playerRef.current
    if (!player || !socket) return
    socket.send(type, {
      position: player.getTime(),
      is_playing: !player.isPaused(),
    })
  }

  const hostHandlers = isHost
    ? {
        onPlay: () => sendHostAction('player.play'),
        onPause: () => sendHostAction('player.pause'),
        onSeeked: () => sendHostAction('player.seek'),
      }
    : null

  return { hostHandlers }
}
