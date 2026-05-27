import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import AuthLayout from '../components/auth/AuthLayout.jsx'
import TextField from '../components/ui/TextField.jsx'
import Button from '../components/ui/Button.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { register } from '../api/auth.js'
import { extractError, extractFieldErrors } from '../api/errors.js'

// Экран регистрации: имя пользователя + пароль. После успеха — сразу вход.
export default function RegisterPage() {
  const { isAuthenticated, login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '', chat_display_name: '' })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setErrors({})
    setFormError('')
    setLoading(true)
    try {
      const { data } = await register(form)
      login(data)
      navigate('/', { replace: true })
    } catch (err) {
      setErrors(extractFieldErrors(err))
      setFormError(extractError(err, 'Не удалось зарегистрироваться.'))
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <form className="auth-form" onSubmit={submit} noValidate>
        <p className="auth-section-title">Создание аккаунта</p>
        <TextField
          label="Имя пользователя"
          name="username"
          placeholder="username"
          hint="Латиница, цифры и символы . _ - + — минимум 3 символа"
          value={form.username}
          onChange={update('username')}
          error={errors.username}
          required
        />
        <TextField
          label="Пароль"
          name="password"
          type="password"
          placeholder="Минимум 8 символов"
          value={form.password}
          onChange={update('password')}
          error={errors.password}
          required
        />
        <TextField
          label="Имя в чате"
          name="chat_display_name"
          placeholder="Как вас видно в комнатах (необязательно)"
          value={form.chat_display_name}
          onChange={update('chat_display_name')}
          error={errors.chat_display_name}
        />
        {formError && Object.keys(errors).length === 0 && (
          <p className="auth-error">{formError}</p>
        )}
        <Button type="submit" fullWidth loading={loading}>
          Зарегистрироваться
        </Button>
        <p className="auth-required-note">* поле, обязательное для заполнения</p>
      </form>
    </AuthLayout>
  )
}
