/**
 * Server-Sent Events (SSE) React hooks and utilities for real-time updates.
 * 
 * This module provides React hooks for managing SSE connections, handling
 * real-time events, and integrating with the admin interface components.
 */

import React, { useEffect, useRef, useState, useCallback, createContext, useContext } from 'react';
import type { Display, Slideshow } from '../types';

// SSE Event Types
export interface SSEEvent {
  event_type: string;
  data: unknown;
  event_id?: string;
  timestamp: string;
}

// Specific event data types for type safety
export interface DisplayEventData {
  display_id: number;
  display_name: string;
  is_online?: boolean;
  display?: Display;
  // Assignment-related fields
  slideshow_id?: number;
  slideshow_name?: string;
}

export interface SlideshowEventData {
  slideshow_id: number;
  slideshow_name?: string;
  slideshow?: Slideshow;
}

// SSE Connection States
export type SSEConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error';

// SSE Context
interface SSEContextType {
  connectionState: SSEConnectionState;
  lastEvent: SSEEvent | null;
  eventHistory: SSEEvent[];
  connect: () => void;
  disconnect: () => void;
  addEventListener: (eventType: string, handler: (event: SSEEvent) => void) => () => void;
}

const SSEContext = createContext<SSEContextType | null>(null);

// Calculate exponential backoff with jitter
function calculateBackoff(
  attempt: number,
  baseDelay: number,
  maxDelay: number
): number {
  const exponentialDelay = baseDelay * Math.pow(2, attempt);
  const jitter = exponentialDelay * (0.75 + Math.random() * 0.5);
  return Math.min(jitter, maxDelay);
}

// SSE Hook for managing connections
export function useSSE(endpoint: string, options?: {
  autoConnect?: boolean;
  baseReconnectInterval?: number;
  maxReconnectInterval?: number;
  maxReconnectAttempts?: number;
}) {
  const {
    autoConnect = true,
    baseReconnectInterval = 1000,
    maxReconnectInterval = 30000,
    maxReconnectAttempts = 10
  } = options || {};

  const [connectionState, setConnectionState] = useState<SSEConnectionState>('disconnected');
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [eventHistory, setEventHistory] = useState<SSEEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventHandlersRef = useRef<Map<string, ((event: SSEEvent) => void)[]>>(new Map());
  const connectRef = useRef<() => void>();

  // Add event listener
  const addEventListener = useCallback((eventType: string, handler: (event: SSEEvent) => void) => {
    const handlers = eventHandlersRef.current.get(eventType) || [];
    handlers.push(handler);
    eventHandlersRef.current.set(eventType, handlers);

    // Return cleanup function
    return () => {
      const currentHandlers = eventHandlersRef.current.get(eventType) || [];
      const index = currentHandlers.indexOf(handler);
      if (index > -1) {
        currentHandlers.splice(index, 1);
        if (currentHandlers.length === 0) {
          eventHandlersRef.current.delete(eventType);
        } else {
          eventHandlersRef.current.set(eventType, currentHandlers);
        }
      }
    };
  }, []);

  // Handle incoming SSE events
  const handleEvent = useCallback((eventType: string, eventData: unknown) => {
    const event: SSEEvent = {
      event_type: eventType,
      data: eventData,
      timestamp: new Date().toISOString()
    };

    setLastEvent(event);
    setEventHistory(prev => [...prev.slice(-99), event]); // Keep last 100 events

    // Call registered handlers
    const handlers = eventHandlersRef.current.get(eventType) || [];
    handlers.forEach(handler => {
      try {
        handler(event);
      } catch (error) {
        console.error(`Error in SSE event handler for ${eventType}:`, error);
      }
    });

    // Call general event handlers
    const generalHandlers = eventHandlersRef.current.get('*') || [];
    generalHandlers.forEach(handler => {
      try {
        handler(event);
      } catch (error) {
        console.error('Error in general SSE event handler:', error);
      }
    });
  }, []);

  // Connect to SSE endpoint
  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      return; // Already connected
    }

    setConnectionState('connecting');
    setError(null);

    try {
      const eventSource = new EventSource(endpoint, {
        withCredentials: true
      });

      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setConnectionState('connected');
        reconnectAttemptsRef.current = 0;
        console.log('SSE connection established');
      };

      eventSource.onerror = (event) => {
        console.error('SSE connection error:', event);
        setConnectionState('error');
        setError('Connection error occurred');

        // Close and attempt reconnect
        eventSource.close();
        eventSourceRef.current = null;

        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = calculateBackoff(
            reconnectAttemptsRef.current,
            baseReconnectInterval,
            maxReconnectInterval
          );
          reconnectAttemptsRef.current++;
          console.log(
            `SSE reconnection attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts} ` +
            `in ${Math.round(delay)}ms`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            if (reconnectAttemptsRef.current <= maxReconnectAttempts) {
              connectRef.current?.();
            }
          }, delay);
        } else {
          console.error('SSE max reconnection attempts exceeded');
          setConnectionState('disconnected');
        }
      };

      // Handle different event types
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleEvent('message', data);
        } catch (error) {
          console.error('Error parsing SSE message:', error);
        }
      };

      // Handle specific event types
      const eventTypes = [
        'connected', 'ping', 'display.status_changed', 'display.assignment_changed',
        'display.configuration_changed', 'slideshow.updated', 'slideshow.created',
        'slideshow.deleted', 'system.notification'
      ];

      eventTypes.forEach(eventType => {
        eventSource.addEventListener(eventType, (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            handleEvent(eventType, data);
          } catch (error) {
            console.error(`Error parsing SSE event ${eventType}:`, error);
          }
        });
      });

    } catch (error) {
      console.error('Error creating SSE connection:', error);
      setConnectionState('error');
      setError('Failed to create connection');
    }
  }, [endpoint, handleEvent, maxReconnectAttempts, baseReconnectInterval, maxReconnectInterval]);

  // Keep connectRef updated so reconnection can access the latest connect function
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  // Disconnect from SSE
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setConnectionState('disconnected');
    reconnectAttemptsRef.current = 0;
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    let connectTimer: ReturnType<typeof setTimeout> | null = null;

    if (autoConnect) {
      // Defer connect to avoid synchronous setState within effect
      connectTimer = setTimeout(() => {
        connect();
      }, 0);
    }

    // Cleanup on unmount
    return () => {
      if (connectTimer) {
        clearTimeout(connectTimer);
      }
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Handle page visibility changes (reconnect when page becomes visible)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && connectionState === 'error') {
        connect();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [connect, connectionState]);

  return {
    connectionState,
    lastEvent,
    eventHistory,
    error,
    connect,
    disconnect,
    addEventListener
  };
}

// Hook for display-specific events
export function useDisplayEvents(onDisplayUpdate?: (display: Display) => void) {
  const sse = useSSE('/api/v1/events/admin');

  useEffect(() => {
    if (!onDisplayUpdate) return;

    const cleanupHandlers: (() => void)[] = [];

    // Listen for display status changes
    cleanupHandlers.push(
      sse.addEventListener('display.status_changed', (event) => {
        const eventData = event.data as DisplayEventData;
        // Extract the display object from the event data
        const display = eventData.display || eventData;
        onDisplayUpdate(display as Display);
      })
    );

    // Listen for display assignment changes
    cleanupHandlers.push(
      sse.addEventListener('display.assignment_changed', (event) => {
        const eventData = event.data as DisplayEventData;
        // Extract the display object from the event data
        const display = eventData.display || eventData;
        onDisplayUpdate(display as Display);
      })
    );

    // Listen for display configuration changes
    cleanupHandlers.push(
      sse.addEventListener('display.configuration_changed', (event) => {
        const eventData = event.data as DisplayEventData;
        // Extract the display object from the event data
        const display = eventData.display || eventData;
        onDisplayUpdate(display as Display);
      })
    );

    return () => {
      cleanupHandlers.forEach(cleanup => cleanup());
    };
  }, [sse, onDisplayUpdate]);

  return sse;
}

// Hook for slideshow-specific events
export function useSlideshowEvents(onSlideshowUpdate?: (slideshow: Slideshow) => void) {
  const sse = useSSE('/api/v1/events/admin');

  useEffect(() => {
    if (!onSlideshowUpdate) return;

    const cleanupHandlers: (() => void)[] = [];

    // Listen for slideshow events
    const slideshowEvents = ['slideshow.created', 'slideshow.updated', 'slideshow.deleted'];
    
    slideshowEvents.forEach(eventType => {
      cleanupHandlers.push(
        sse.addEventListener(eventType, (event) => {
          onSlideshowUpdate(event.data as Slideshow);
        })
      );
    });

    return () => {
      cleanupHandlers.forEach(cleanup => cleanup());
    };
  }, [sse, onSlideshowUpdate]);

  return sse;
}

// SSE Status Indicator Component
export function SSEStatusIndicator({ sse }: { sse: ReturnType<typeof useSSE> }) {
  const getStatusColor = () => {
    switch (sse.connectionState) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      case 'disconnected': return 'text-gray-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = () => {
    switch (sse.connectionState) {
      case 'connected': return '●';
      case 'connecting': return '◐';
      case 'error': return '✕';
      case 'disconnected': return '○';
      default: return '○';
    }
  };

  const getStatusText = () => {
    switch (sse.connectionState) {
      case 'connected': return 'Live Updates';
      case 'connecting': return 'Connecting...';
      case 'error': return 'Connection Error';
      case 'disconnected': return 'Disconnected';
      default: return 'Unknown';
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
      <span className="text-lg">{getStatusIcon()}</span>
      <span className="text-sm">{getStatusText()}</span>
      {sse.error && (
        <span className="text-xs text-red-400">({sse.error})</span>
      )}
    </div>
  );
}

// SSE Provider Component
export function SSEProvider({ children }: { children: React.ReactNode }) {
  const sse = useSSE('/api/v1/events/admin');

  const contextValue: SSEContextType = {
    connectionState: sse.connectionState,
    lastEvent: sse.lastEvent,
    eventHistory: sse.eventHistory,
    connect: sse.connect,
    disconnect: sse.disconnect,
    addEventListener: sse.addEventListener
  };

  return (
    <SSEContext.Provider value={contextValue}>
      {children}
    </SSEContext.Provider>
  );
}

// Hook to use SSE context
export function useSSEContext() {
  const context = useContext(SSEContext);
  if (!context) {
    throw new Error('useSSEContext must be used within SSEProvider');
  }
  return context;
}

// Hook to track network/online status
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Track if we were offline to show reconnection message
      if (!navigator.onLine) {
        setWasOffline(true);
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      setWasOffline(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const clearWasOffline = useCallback(() => {
    setWasOffline(false);
  }, []);

  return { isOnline, wasOffline, clearWasOffline };
}

// Offline Banner Component - displays when network is unavailable
export function OfflineBanner() {
  const { isOnline, wasOffline, clearWasOffline } = useNetworkStatus();
  const [showReconnected, setShowReconnected] = useState(false);

  useEffect(() => {
    if (isOnline && wasOffline) {
      setShowReconnected(true);
      const timer = setTimeout(() => {
        setShowReconnected(false);
        clearWasOffline();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [isOnline, wasOffline, clearWasOffline]);

  if (!isOnline) {
    return (
      <div
        className="alert alert-warning d-flex align-items-center mb-0 rounded-0"
        role="alert"
        style={{ position: 'sticky', top: 0, zIndex: 1050 }}
      >
        <i className="bi bi-wifi-off me-2"></i>
        <div>
          <strong>You are offline.</strong> Some features may not be available.
          Changes will sync when connection is restored.
        </div>
      </div>
    );
  }

  if (showReconnected) {
    return (
      <div
        className="alert alert-success d-flex align-items-center mb-0 rounded-0"
        role="alert"
        style={{ position: 'sticky', top: 0, zIndex: 1050 }}
      >
        <i className="bi bi-wifi me-2"></i>
        <div>
          <strong>Back online!</strong> Connection restored.
        </div>
      </div>
    );
  }

  return null;
}

// Connection Status Badge - Bootstrap-styled status indicator
export function ConnectionStatusBadge({ sse }: { sse: ReturnType<typeof useSSE> }) {
  const getBadgeClass = () => {
    switch (sse.connectionState) {
      case 'connected':
        return 'bg-success';
      case 'connecting':
        return 'bg-warning';
      case 'error':
        return 'bg-danger';
      case 'disconnected':
        return 'bg-secondary';
      default:
        return 'bg-secondary';
    }
  };

  const getStatusText = () => {
    switch (sse.connectionState) {
      case 'connected':
        return 'Live';
      case 'connecting':
        return 'Connecting';
      case 'error':
        return 'Error';
      case 'disconnected':
        return 'Offline';
      default:
        return 'Unknown';
    }
  };

  return (
    <span className={`badge ${getBadgeClass()}`}>
      <i className="bi bi-broadcast me-1"></i>
      {getStatusText()}
    </span>
  );
}

// Connection Health Monitor - tracks connection quality
export function useConnectionHealth(sse: ReturnType<typeof useSSE>) {
  const [health, setHealth] = useState<{
    latency: number | null;
    lastPingTime: Date | null;
    missedPings: number;
  }>({
    latency: null,
    lastPingTime: null,
    missedPings: 0,
  });

  useEffect(() => {
    let pingTimeout: ReturnType<typeof setTimeout> | null = null;
    const expectedPingInterval = 30000; // Expected ping every 30 seconds

    const resetPingTimeout = () => {
      if (pingTimeout) {
        clearTimeout(pingTimeout);
      }
      pingTimeout = setTimeout(() => {
        setHealth((prev) => ({
          ...prev,
          missedPings: prev.missedPings + 1,
        }));
      }, expectedPingInterval + 5000); // 5 second grace period
    };

    // Listen for ping events
    const cleanup = sse.addEventListener('ping', (event) => {
      const now = new Date();
      const eventTime = event.timestamp ? new Date(event.timestamp) : now;
      const latency = now.getTime() - eventTime.getTime();

      setHealth({
        latency: Math.max(0, latency),
        lastPingTime: now,
        missedPings: 0,
      });

      resetPingTimeout();
    });

    // Start monitoring when connected
    if (sse.connectionState === 'connected') {
      resetPingTimeout();
    }

    return () => {
      cleanup();
      if (pingTimeout) {
        clearTimeout(pingTimeout);
      }
    };
  }, [sse, sse.connectionState]);

  const isHealthy = sse.connectionState === 'connected' && health.missedPings < 2;

  return {
    ...health,
    isHealthy,
    connectionState: sse.connectionState,
  };
}
