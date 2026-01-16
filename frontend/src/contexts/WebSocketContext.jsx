import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const WebSocketContext = createContext(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    // Return default values if not in provider (e.g., during initial render)
    return {
      connected: false,
      notifications: [],
      unreadCount: 0,
      markAllAsRead: () => {},
      clearNotifications: () => {},
      reconnect: () => {},
      loading: false,
    };
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const { user, token, isAuthenticated } = useAuth();
  const [connected, setConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);
  const connectFnRef = useRef(null);

  // Fetch past notifications from API
  const fetchNotifications = useCallback(async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${BACKEND_URL}/api/notifications`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { limit: 50 }
      });
      
      const data = response.data;
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Handle incoming notification
  const handleNotification = useCallback((notification) => {
    // Add to notifications list (at the beginning)
    setNotifications(prev => [notification, ...prev].slice(0, 50)); // Keep last 50
    setUnreadCount(prev => prev + 1);

    // Show toast notification based on type
    const { type, title, message, amount } = notification;
    
    switch (type) {
      case 'deposit_request':
        toast.info(title, {
          description: `${message}${amount ? ` - $${amount.toLocaleString()}` : ''}`,
          duration: 5000,
        });
        break;
      case 'withdrawal_request':
        toast.warning(title, {
          description: `${message}${amount ? ` - $${amount.toLocaleString()}` : ''}`,
          duration: 5000,
        });
        break;
      case 'transaction_status':
        toast.success(title, {
          description: message,
          duration: 5000,
        });
        break;
      case 'trade_signal':
        toast(title, {
          description: message,
          duration: 8000,
          icon: '📊',
        });
        break;
      case 'system_announcement':
        toast.info(title, {
          description: message,
          duration: 10000,
        });
        break;
      default:
        toast(title, {
          description: message,
          duration: 5000,
        });
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!isAuthenticated || !user || !token) return;
    
    // Fetch past notifications first
    fetchNotifications();
    
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Get WebSocket URL from backend URL
    // The WebSocket endpoint is NOT prefixed with /api - it's directly on /ws/
    const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
    const wsProtocol = backendUrl.startsWith('https') ? 'wss' : 'ws';
    const wsHost = backendUrl.replace(/^https?:\/\//, '');
    const wsUrl = `${wsProtocol}://${wsHost}/ws/${user.id}?token=${token}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        
        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000); // Ping every 30 seconds
      };

      ws.onmessage = (event) => {
        if (event.data === 'pong') return; // Ignore pong responses
        
        try {
          const notification = JSON.parse(event.data);
          handleNotification(notification);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code);
        setConnected(false);
        
        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }
        
        // Attempt to reconnect after 5 seconds (unless intentionally closed)
        if (event.code !== 1000 && isAuthenticated) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect WebSocket...');
            // Use ref to call connect to avoid stale closure
            if (connectFnRef.current) {
              connectFnRef.current();
            }
          }, 5000);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [isAuthenticated, user, token, handleNotification, fetchNotifications]);

  // Keep connectFnRef in sync with connect
  useEffect(() => {
    connectFnRef.current = connect;
  }, [connect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000); // Normal closure
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  const markAllAsRead = useCallback(async () => {
    setUnreadCount(0);
    // Mark as read in backend
    if (token) {
      try {
        await axios.post(`${BACKEND_URL}/api/notifications/mark-read`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } catch (error) {
        console.error('Failed to mark notifications as read:', error);
      }
    }
  }, [token]);

  const clearNotifications = useCallback(async () => {
    setNotifications([]);
    setUnreadCount(0);
    // Delete in backend
    if (token) {
      try {
        await axios.delete(`${BACKEND_URL}/api/notifications`, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } catch (error) {
        console.error('Failed to clear notifications:', error);
      }
    }
  }, [token]);

  // Connect when authenticated
  useEffect(() => {
    if (isAuthenticated && user && token) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [isAuthenticated, user, token, connect, disconnect]);

  const value = {
    connected,
    notifications,
    unreadCount,
    markAllAsRead,
    clearNotifications,
    reconnect: connect,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export default WebSocketContext;
