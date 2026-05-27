import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TextField from './TextField.jsx'

describe('TextField', () => {
  it('показывает подпись и поле ввода', () => {
    render(<TextField label="Электронная почта" name="email" />)
    expect(screen.getByText('Электронная почта')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('отображает текст ошибки и класс состояния ошибки', () => {
    const { container } = render(<TextField label="Почта" error="Неверный формат" />)
    expect(screen.getByText('Неверный формат')).toBeInTheDocument()
    expect(container.querySelector('.field--error')).not.toBeNull()
  })

  it('при ошибке подсказка не показывается', () => {
    render(<TextField label="Почта" hint="подсказка" error="ошибка" />)
    expect(screen.queryByText('подсказка')).toBeNull()
  })
})
