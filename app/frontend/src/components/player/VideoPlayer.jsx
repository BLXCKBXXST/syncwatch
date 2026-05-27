import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'
import './VideoPlayer.css'

// Плеер-обёртка над <video>. Через ref наружу выдаёт императивное управление —
// нужно для синхронизации в комнатах совместного просмотра. Поддерживает
// HLS (.m3u8) через динамический импорт hls.js — на сайтах без нативного HLS
// (всё кроме Safari).
const VideoPlayer = forwardRef(function VideoPlayer(
  {
    src,
    poster,
    controls = true,
    autoPlay = false,
    className = '',
    onPlay,
    onPause,
    onSeeked,
    onTimeUpdate,
    onEnded,
    onError,
  },
  ref,
) {
  const videoRef = useRef(null)

  useImperativeHandle(
    ref,
    () => ({
      play: () => videoRef.current?.play().catch(() => {}),
      pause: () => videoRef.current?.pause(),
      seek: (time) => {
        if (videoRef.current) videoRef.current.currentTime = time
      },
      getTime: () => videoRef.current?.currentTime ?? 0,
      getDuration: () => videoRef.current?.duration ?? 0,
      isPaused: () => videoRef.current?.paused ?? true,
      setPlaybackRate: (rate) => {
        if (videoRef.current) videoRef.current.playbackRate = rate
      },
    }),
    [],
  )

  // Подключение hls.js, если поток m3u8 и нативно не играется (вне Safari).
  useEffect(() => {
    const videoEl = videoRef.current
    if (!videoEl || !src) return undefined
    const isHls = /\.m3u8(\?|#|$)/i.test(src)
    const canNative = videoEl.canPlayType('application/vnd.apple.mpegurl')
    if (!isHls || canNative) {
      videoEl.src = src
      return undefined
    }
    let hls
    let cancelled = false
    import('hls.js').then(({ default: Hls }) => {
      if (cancelled || !videoRef.current) return
      if (!Hls.isSupported()) {
        videoRef.current.src = src
        return
      }
      hls = new Hls({ enableWorker: true })
      hls.loadSource(src)
      hls.attachMedia(videoRef.current)
    })
    return () => {
      cancelled = true
      if (hls) hls.destroy()
    }
  }, [src])

  return (
    <div className={`player ${className}`.trim()}>
      <video
        ref={videoRef}
        poster={poster}
        controls={controls}
        autoPlay={autoPlay}
        playsInline
        className="player__video"
        onPlay={onPlay}
        onPause={onPause}
        onSeeked={onSeeked}
        onTimeUpdate={onTimeUpdate}
        onEnded={onEnded}
        onError={onError}
      />
    </div>
  )
})

export default VideoPlayer
