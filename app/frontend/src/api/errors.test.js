import { describe, it, expect } from 'vitest'
import { extractError, extractFieldErrors } from './errors.js'

describe('extractError', () => {
  it('берёт сообщение из detail', () => {
    const err = { response: { data: { detail: 'Нет доступа' } } }
    expect(extractError(err)).toBe('Нет доступа')
  })

  it('берёт первую ошибку поля', () => {
    const err = { response: { data: { email: ['E-mail занят'] } } }
    expect(extractError(err)).toBe('E-mail занят')
  })

  it('возвращает фолбэк при пустом ответе', () => {
    expect(extractError({}, 'Ошибка')).toBe('Ошибка')
  })
})

describe('extractFieldErrors', () => {
  it('собирает карту «поле → сообщение»', () => {
    const err = { response: { data: { email: ['Занят'], title: ['Пусто'] } } }
    expect(extractFieldErrors(err)).toEqual({ email: 'Занят', title: 'Пусто' })
  })

  it('пустой ответ — пустая карта', () => {
    expect(extractFieldErrors({})).toEqual({})
  })
})
