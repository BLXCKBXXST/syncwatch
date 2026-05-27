// Чистая логика коррекции рассинхронизации плеера зрителя.
// Вынесено отдельно от хука, чтобы легко покрыть юнит-тестами.

export const HARD_DRIFT = 1.0 // секунд — резкая перемотка
export const SOFT_DRIFT = 0.3 // секунд — мягкая подстройка скоростью

// Ожидаемая позиция воспроизведения в момент nowSeconds на основе последнего
// снимка состояния комнаты base = { position, isPlaying, clientTime }.
export function expectedPosition(base, nowSeconds) {
  if (!base) return 0
  if (!base.isPlaying) return base.position
  return base.position + (nowSeconds - base.clientTime)
}

// Решение по величине рассинхрона (drift = время плеера − ожидаемое время).
//  > 1.0 c     — резкая перемотка к ожидаемой позиции;
//  0.3..1.0 c  — плавная подстройка скоростью воспроизведения;
//  < 0.3 c     — ничего не делаем.
export function syncDecision(drift) {
  const magnitude = Math.abs(drift)
  if (magnitude > HARD_DRIFT) return { action: 'seek', rate: 1 }
  if (magnitude > SOFT_DRIFT) return { action: 'rate', rate: drift > 0 ? 0.95 : 1.05 }
  return { action: 'none', rate: 1 }
}
