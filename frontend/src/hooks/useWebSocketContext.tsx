import { useState, useEffect, createContext, useContext } from 'react';
import { createWebSocketConnection } from '../lib/api';

interface WebSocketContextType {
  ws: WebSocket | null;
  isConnected: boolean;
  send: (data: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType>({
  ws: null,
  isConnected: false,
  send: () => {},
});

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const connection = createWebSocketConnection();
    
    if (connection) {
      connection.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };
      
      connection.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      };
      
      setWs(connection);
    }
    
    return () => {
      if (connection) {
        connection.close();
      }
    };
  }, []);

  const send = (data: any) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    }
  };

  return (
    <WebSocketContext.Provider value={{ ws, isConnected, send }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  return useContext(WebSocketContext);
}
