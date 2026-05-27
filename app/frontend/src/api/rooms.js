import client from './client.js'

// Функции обращения к эндпоинтам комнат совместного просмотра.
export const createRoom = (data) => client.post('/rooms/', data)
export const getRoom = (id) => client.get(`/rooms/${id}/`)
export const listMyRooms = () => client.get('/rooms/')
export const refreshStream = (id) => client.post(`/rooms/${id}/refresh-stream/`)
export const transferHost = (id, participantId) =>
  client.post(`/rooms/${id}/transfer-host/`, { participant_id: participantId })
