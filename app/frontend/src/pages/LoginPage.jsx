import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import AuthLayout from '../components/auth/AuthLayout.jsx'
import TextField from '../components/ui/TextField.jsx'
import Button from '../components/ui/Button.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { guestLogin, login as loginRequest } from '../api/auth.js'
import { extractError } from '../api/errors.js'

// Экран входа: имя пользователя + пароль либо вход гостем.
export default function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [guestLoading, setGuestLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const finish = (data) => {
    login(data)
    navigate('/', { replace: true })
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await loginRequest(form)
      finish(data)
    } catch (err) {
      setError(extractError(err, 'Не удалось войти.'))
      setLoading(false)
    }
  }

  const enterAsGuest = async () => {
    setError('')
    setGuestLoading(true)
    try {
      const { data } = await guestLogin()
      finish(data)
    } catch (err) {
      setError(extractError(err, 'Не удалось создать гостевой аккаунт.'))
      setGuestLoading(false)
    }
  }

  return (
    <AuthLayout>
      <form className="auth-form" onSubmit={submit} noValidate>
        <p className="auth-section-title">Вход в аккаунт</p>
        <TextField
          label="Имя пользователя"
          name="username"
          placeholder="username"
          value={form.username}
          onChange={update('username')}
          required
        />
        <TextField
          label="Пароль"
          name="password"
          type="password"
          placeholder="Ваш пароль"
          value={form.password}
          onChange={update('password')}
          required
        />
        {error && <p className="auth-error">{error}</p>}
        <Button type="submit" fullWidth loading={loading}>
          Войти
        </Button>
      </form>

      <div className="auth-alt">
        <div className="auth-divider">
          <span>или</span>
        </div>
        <Button
          variant="secondary"
          fullWidth
          loading={guestLoading}
          onClick={enterAsGuest}
        >
          Войти как гостем
        </Button>
        <p className="auth-note auth-note--center">
          Гостевой аккаунт временный — он удаляется после 24 часов простоя
          вместе со всеми загруженными видео и комнатами.
        </p>
      </div>
    </AuthLayout>
  )
}
