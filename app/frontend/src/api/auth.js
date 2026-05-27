import client from './client.js'

// Функции обращения к эндпоинтам авторизации и профиля.
export const register = (data) => client.post('/auth/register/', data)
export const login = (data) => client.post('/auth/login/', data)
export const guestLogin = () => client.post('/auth/guest/')
export const getMe = () => client.get('/auth/me/')
export const updateMe = (data) => client.patch('/auth/me/', data)
export const logoutAll = () => client.post('/auth/logout-all/')
