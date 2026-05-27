import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getQuestions } from '../../api/chat.js'
import Button from '../ui/Button.jsx'

// Вкладка «Вопрос/ответ»: вопросы зрителей, ответы и голоса.
export default function QAPanel({ socket, roomId, canPost }) {
  const [questions, setQuestions] = useState([])
  const [newQuestion, setNewQuestion] = useState('')
  const [answerFor, setAnswerFor] = useState(null)
  const [answerText, setAnswerText] = useState('')

  useEffect(() => {
    getQuestions(roomId)
      .then(({ data }) => setQuestions(data))
      .catch(() => {})
  }, [roomId])

  useEffect(() => {
    if (!socket) return undefined
    const offQuestion = socket.on('qa.question', (event) => {
      setQuestions((prev) => [...prev, event.question])
    })
    const offAnswer = socket.on('qa.answer', (event) => {
      setQuestions((prev) =>
        prev.map((q) =>
          q.id === event.question_id
            ? { ...q, is_answered: true, answers: [...q.answers, event.answer] }
            : q,
        ),
      )
    })
    const offUpvote = socket.on('qa.upvote', (event) => {
      setQuestions((prev) =>
        prev.map((q) =>
          q.id === event.question_id ? { ...q, upvotes_count: event.upvotes_count } : q,
        ),
      )
    })
    return () => {
      offQuestion()
      offAnswer()
      offUpvote()
    }
  }, [socket])

  const ask = (e) => {
    e.preventDefault()
    const value = newQuestion.trim()
    if (!value || !socket) return
    socket.send('qa.question', { text: value })
    setNewQuestion('')
  }

  const sendAnswer = (questionId) => {
    const value = answerText.trim()
    if (!value || !socket) return
    socket.send('qa.answer', { question_id: questionId, text: value })
    setAnswerText('')
    setAnswerFor(null)
  }

  return (
    <div className="rpanel">
      <div className="rpanel__list">
        {questions.length === 0 && (
          <p className="rpanel__empty">Вопросов пока нет.</p>
        )}
        {questions.map((q) => (
          <div key={q.id} className="qa">
            <div className="qa__head">
              <button
                type="button"
                className="qa__vote"
                onClick={() => canPost && socket?.send('qa.upvote', { question_id: q.id })}
                disabled={!canPost}
                aria-label="Голосовать за вопрос"
              >
                ▲ {q.upvotes_count}
              </button>
              <div className="qa__body">
                <span className="qa__author">{q.display_name}</span>
                <p className="qa__text">{q.text}</p>
              </div>
              {q.is_answered && <span className="qa__badge">отвечен</span>}
            </div>

            {q.answers.map((a) => (
              <div key={a.id} className="qa__answer">
                <span className="qa__author">{a.display_name}</span>
                <p className="qa__text">{a.text}</p>
              </div>
            ))}

            {canPost && answerFor === q.id && (
              <div className="qa__answer-form">
                <input
                  className="rpanel__input"
                  placeholder="Ваш ответ"
                  value={answerText}
                  onChange={(e) => setAnswerText(e.target.value)}
                  autoFocus
                />
                <Button onClick={() => sendAnswer(q.id)} disabled={!answerText.trim()}>
                  Ответить
                </Button>
              </div>
            )}
            {canPost && answerFor !== q.id && (
              <button
                type="button"
                className="qa__answer-link"
                onClick={() => {
                  setAnswerFor(q.id)
                  setAnswerText('')
                }}
              >
                Ответить
              </button>
            )}
          </div>
        ))}
      </div>

      {canPost ? (
        <form className="rpanel__composer" onSubmit={ask}>
          <input
            className="rpanel__input"
            placeholder="Задать вопрос"
            value={newQuestion}
            maxLength={1000}
            onChange={(e) => setNewQuestion(e.target.value)}
          />
          <Button type="submit" fullWidth disabled={!newQuestion.trim()}>
            Спросить
          </Button>
        </form>
      ) : (
        <Link to="/login" className="rpanel__guest">
          Войдите, чтобы задавать вопросы
        </Link>
      )}
    </div>
  )
}
