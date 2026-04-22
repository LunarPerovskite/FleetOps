import { useState, useEffect, useRef } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  
  useEffect(() => {
    const token = localStorage.getItem('fleetops_token');
    if (!token) return;
    
    const connect = () => {
      try {
        const ws = new WebSocket(`${WS_URL}?token=${token}`);
        
        ws.onopen = () => {
          console.log('WebSocket connected');
          setIsConnected(true);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLastMessage(data);
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };
        
        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setIsConnected(false);
          
          // Reconnect after 5 seconds
          reconnectTimeoutRef.current = setTimeout(connect, 5000);
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
        
        wsRef.current = ws;
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
      }
    };
    
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
  
  const send = (data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  };
  
  return {
    ws: wsRef.current,
    isConnected,
    lastMessage,
    send,
  };
}
