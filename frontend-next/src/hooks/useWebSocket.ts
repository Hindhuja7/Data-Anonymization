import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageHandlersRef = useRef<Map<string, (data: any) => void>>(new Map());
  const globalHandlerRef = useRef<((data: any) => void) | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected successfully');
      };

      ws.onmessage = (event) => {
        try {
          const rawData = JSON.parse(event.data);
          setLastMessage(rawData);

          // Invoke global fallback handler if set
          if (globalHandlerRef.current) {
            globalHandlerRef.current(rawData);
          }

          // Route to specific message type handler if registered
          if (rawData && rawData.type) {
            const handler = messageHandlersRef.current.get(rawData.type);
            if (handler) {
              handler(rawData);
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.warn('WebSocket transient connection warning (polling fallback active):', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected, scheduling reconnect...');
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  }, [url]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, []);

  // Support both onMessage(type, handler) AND onMessage(handler)
  const onMessage = useCallback((arg1: string | ((data: any) => void), arg2?: (data: any) => void) => {
    if (typeof arg1 === 'string' && arg2) {
      messageHandlersRef.current.set(arg1, arg2);
      return () => {
        messageHandlersRef.current.delete(arg1);
      };
    } else if (typeof arg1 === 'function') {
      globalHandlerRef.current = arg1;
      return () => {
        globalHandlerRef.current = null;
      };
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    onMessage,
    connect,
    disconnect,
  };
}
