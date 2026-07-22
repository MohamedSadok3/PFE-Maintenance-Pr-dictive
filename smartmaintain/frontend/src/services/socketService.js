import { io } from 'socket.io-client'
import { SOCKET_URL } from './api'

// Singleton socket instance — one connection shared across the whole app.
// Creating a new io() on every hook mount caused multiple overlapping
// connections that flooded each other and starved the real-time feed.
let _socket = null

export function getSocket() {
  if (!_socket) {
    _socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      autoConnect: false,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 10000,
    })
  }
  return _socket
}

// Keep createSocket as an alias for backwards compatibility with any
// other callers (e.g. useDashboard).
export function createSocket() {
  return getSocket()
}
