import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import MessageCard from './MessageCard.jsx'

const message = { id: '1', display_name: 'Нина', text: 'Всем привет', likes_count: 3 }

describe('MessageCard', () => {
  it('показывает автора, текст и счётчик лайков', () => {
    render(<MessageCard message={message} liked={false} onLike={() => {}} />)
    expect(screen.getByText('Нина')).toBeInTheDocument()
    expect(screen.getByText('Всем привет')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('вызывает onLike по клику на сердечко', () => {
    const onLike = vi.fn()
    render(<MessageCard message={message} liked onLike={onLike} />)
    screen.getByRole('button', { name: 'Нравится' }).click()
    expect(onLike).toHaveBeenCalledOnce()
  })
})
