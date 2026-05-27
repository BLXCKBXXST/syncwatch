import client from './client.js'

// Функции обращения к эндпоинтам видео.
export const listVideos = (params) => client.get('/videos/', { params })
export const getVideo = (id) => client.get(`/videos/${id}/`)
export const myVideos = (params) => client.get('/videos/mine/', { params })
export const updateVideo = (id, data) => client.patch(`/videos/${id}/`, data)
export const deleteVideo = (id) => client.delete(`/videos/${id}/`)

export const uploadVideo = (formData, onUploadProgress) =>
  client.post('/videos/', formData, { onUploadProgress })
