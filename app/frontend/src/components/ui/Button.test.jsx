import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Button from './Button.jsx'

describe('Button', () => {
  it('рендерит текст и класс варианта', () => {
    render(<Button variant="secondary">Готово</Button>)
    const button = screen.getByRole('button', { name: 'Готово' })
    expect(button).toHaveClass('btn--secondary')
  })

  it('в состоянии загрузки заблокирована', () => {
    render(<Button loading>Сохранить</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('вызывает onClick по нажатию', () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Жми</Button>)
    screen.getByRole('button').click()
    expect(onClick).toHaveBeenCalledOnce()
  })
})
