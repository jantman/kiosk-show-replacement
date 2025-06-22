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

// SSE Hook for managing connections
export function useSSE(endpoint: string, options?: {
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}) {
  const {
    autoConnect = true,
    reconnectInterval = 5000,
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
          reconnectAttemptsRef.current++;
          console.log(`SSE reconnection attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (reconnectAttemptsRef.current <= maxReconnectAttempts) {
              connect();
            }
          }, reconnectInterval);
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
  }, [endpoint, handleEvent, maxReconnectAttempts, reconnectInterval]);

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
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
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
