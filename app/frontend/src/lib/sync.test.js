import { describe, it, expect } from 'vitest'
import { expectedPosition, syncDecision } from './sync.js'

describe('expectedPosition', () => {
  it('на паузе позиция фиксирована', () => {
    const base = { position: 30, isPlaying: false, clientTime: 1000 }
    expect(expectedPosition(base, 1100)).toBe(30)
  })

  it('во время воспроизведения позиция растёт с реальным временем', () => {
    const base = { position: 10, isPlaying: true, clientTime: 1000 }
    expect(expectedPosition(base, 1015)).toBe(25)
  })

  it('без снимка состояния возвращает 0', () => {
    expect(expectedPosition(null, 1000)).toBe(0)
  })
})

describe('syncDecision', () => {
  it('малый дрейф — коррекции нет', () => {
    expect(syncDecision(0.1).action).toBe('none')
  })

  it('средний дрейф вперёд — замедление скоростью', () => {
    const decision = syncDecision(0.6)
    expect(decision.action).toBe('rate')
    expect(decision.rate).toBe(0.95)
  })

  it('среднее отставание — ускорение скоростью', () => {
    expect(syncDecision(-0.6).rate).toBe(1.05)
  })

  it('большой дрейф — резкая перемотка', () => {
    expect(syncDecision(3).action).toBe('seek')
  })
})
