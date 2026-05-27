import client from './client.js'

// История чата и вопросов комнаты (живые события идут по WebSocket).
export const getMessages = (roomId) => client.get(`/rooms/${roomId}/messages/`)
export const getQuestions = (roomId) => client.get(`/rooms/${roomId}/questions/`)
