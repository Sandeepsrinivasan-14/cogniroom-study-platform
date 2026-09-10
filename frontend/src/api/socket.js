import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect(token) {
    if (this.socket) {
      if (this.socket.connected) return;
      this.socket.connect();
      return;
    }

    // Connect without path, standard setup
    this.socket = io('http://localhost:8000', {
      auth: { token },
      transports: ['websocket', 'polling'],
    });

    this.socket.on('connect', () => {
      console.log('Socket connected:', this.socket.id);
    });

    this.socket.on('disconnect', () => {
      console.log('Socket disconnected');
    });

    this.socket.on('error', (err) => {
      console.error('Socket error:', err);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  joinRoom(roomId) {
    if (!this.socket) return;
    
    if (this.socket.connected) {
      this.socket.emit('joinroom', { room_id: roomId });
    } else {
      // If not connected, add a one-time listener to join when connected
      this.socket.once('connect', () => {
        this.socket.emit('joinroom', { room_id: roomId });
      });
    }
  }

  emit(event, data) {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    }
  }

  on(event, callback) {
    if (!this.socket) return;
    this.socket.on(event, callback);
    
    // Store reference for easier cleanup
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.socket) return;
    if (callback) {
      this.socket.off(event, callback);
      const eventListeners = this.listeners.get(event);
      if (eventListeners) {
        this.listeners.set(event, eventListeners.filter(cb => cb !== callback));
      }
    } else {
      this.socket.off(event);
      this.listeners.delete(event);
    }
  }

  // Helper methods for specific events
  sendChatMessage(message, userId, roomId) {
    this.emit('chatmessage', { message, user_id: userId, room_id: roomId });
  }

  sendWhiteboardUpdate(data, roomId) {
    this.emit('whiteboard_update', { ...data, room_id: roomId });
  }

  sendWebcamLoad(loadScore, userId, roomId) {
    this.emit('webcam_load_update', { load_score: loadScore, user_id: userId, room_id: roomId });
  }
}

export const socketService = new SocketService();
