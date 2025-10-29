import { useEffect, useState, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuthStore } from '@/stores/authStore';
import type { WebSocketMessage } from '@/types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const socketRef = useRef<Socket | null>(null);
  const token = useAuthStore((state) => state.token);

  const connect = useCallback(() => {
    if (!token || socketRef.current?.connected) return;

    const socket = io(WS_URL, {
      auth: {
        token,
      },
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
    });

    socket.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });

    socket.on('message', (message: WebSocketMessage) => {
      setMessages((prev) => [...prev, message]);
    });

    socket.on('progress', (message: WebSocketMessage) => {
      setMessages((prev) => [...prev, message]);
    });

    socket.on('error', (error: Error) => {
      console.error('WebSocket error:', error);
    });

    socketRef.current = socket;
  }, [token]);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  useEffect(() => {
    if (token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [token, connect, disconnect]);

  return {
    isConnected,
    messages,
    clearMessages,
    reconnect: connect,
  };
}
