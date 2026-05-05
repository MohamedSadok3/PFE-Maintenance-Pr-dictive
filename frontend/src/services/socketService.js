import { io } from 'socket.io-client'
import { SOCKET_URL } from './api'

export function createSocket() {
  return io(SOCKET_URL, { transports: ['websocket', 'polling'] })
}
