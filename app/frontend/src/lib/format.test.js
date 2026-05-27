import { describe, it, expect } from 'vitest'
import { formatDuration, formatViews } from './format.js'

describe('formatDuration', () => {
  it('форматирует минуты и секунды', () => {
    expect(formatDuration(75)).toBe('1:15')
  })

  it('форматирует часы, минуты и секунды', () => {
    expect(formatDuration(3661)).toBe('1:01:01')
  })

  it('ноль секунд', () => {
    expect(formatDuration(0)).toBe('0:00')
  })
})

describe('formatViews', () => {
  it('малые числа без сокращения', () => {
    expect(formatViews(42)).toBe('42')
  })

  it('тысячи сокращаются', () => {
    expect(formatViews(1500)).toBe('1.5 тыс.')
  })

  it('миллионы сокращаются', () => {
    expect(formatViews(2_400_000)).toBe('2.4 млн')
  })
})
