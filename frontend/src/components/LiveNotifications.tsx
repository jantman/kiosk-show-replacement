/**
 * LiveNotifications - R    notifications.push(
      addEventListener('display.status_changed', (event) => {
        const data = event.data as any;
        const isOnline = data.is_online;
        
        addNotification({
          title: 'Display Status',
          message: `${data.display_name} is now ${isOnline ? 'online' : 'offline'}`,
          variant: isOnline ? 'success' : 'warning'
        });
      })
    );ification component using SSE
 * 
 * Displays toast notifications for real-time events like display status changes,
 * slideshow updates, and assignment modifications.
 */

import React, { useEffect, useState } from 'react';
import { Toast, ToastContainer } from 'react-bootstrap';
import { useSSEContext, DisplayEventData, SlideshowEventData } from '../hooks/useSSE.tsx';

interface Notification {
  id: string;
  title: string;
  message: string;
  variant: 'success' | 'info' | 'warning' | 'danger';
  timestamp: Date;
  show: boolean;
}

const LiveNotifications: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const { addEventListener } = useSSEContext();

  useEffect(() => {
    const eventHandlers: Array<() => void> = [];

    // Display status changes
    eventHandlers.push(
      addEventListener('display.status_changed', (event) => {
        const data = event.data as DisplayEventData;
        const isOnline = data.is_online;
        
        addNotification({
          title: 'Display Status',
          message: `${data.display_name} is now ${isOnline ? 'online' : 'offline'}`,
          variant: isOnline ? 'success' : 'warning'
        });
      })
    );

    // Display assignment changes
    eventHandlers.push(
      addEventListener('display.assignment_changed', (event) => {
        const data = event.data as DisplayEventData;
        const message = data.slideshow_id 
          ? `${data.display_name} assigned to "${data.slideshow_name}"`
          : `${data.display_name} unassigned from slideshow`;
        
        addNotification({
          title: 'Assignment Changed',
          message,
          variant: 'info'
        });
      })
    );

    // Slideshow updates
    eventHandlers.push(
      addEventListener('slideshow.updated', (event) => {
        const data = event.data as SlideshowEventData;
        
        addNotification({
          title: 'Slideshow Updated',
          message: `"${data.slideshow_name}" has been updated`,
          variant: 'info'
        });
      })
    );

    // Slideshow creation
    eventHandlers.push(
      addEventListener('slideshow.created', (event) => {
        const data = event.data as SlideshowEventData;
        
        addNotification({
          title: 'Slideshow Created',
          message: `New slideshow "${data.slideshow_name}" created`,
          variant: 'success'
        });
      })
    );

    // Slideshow deletion
    eventHandlers.push(
      addEventListener('slideshow.deleted', (event) => {
        const data = event.data as SlideshowEventData;
        
        addNotification({
          title: 'Slideshow Deleted',
          message: `Slideshow "${data.slideshow_name}" deleted`,
          variant: 'warning'
        });
      })
    );

    // System events
    eventHandlers.push(
      addEventListener('system.error', (event) => {
        const data = event.data as { message?: string };
        
        addNotification({
          title: 'System Error',
          message: data.message || 'An error occurred',
          variant: 'danger'
        });
      })
    );

    // Cleanup event handlers
    return () => {
      eventHandlers.forEach(cleanup => cleanup());
    };
  }, [addEventListener]);

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'show'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
      show: true
    };

    setNotifications(prev => [newNotification, ...prev.slice(0, 4)]); // Keep only last 5 notifications

    // Auto-hide after 5 seconds
    setTimeout(() => {
      setNotifications(prev => 
        prev.map(n => n.id === newNotification.id ? { ...n, show: false } : n)
      );
    }, 5000);

    // Completely remove after 6 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== newNotification.id));
    }, 6000);
  };

  const dismissNotification = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, show: false } : n)
    );
    
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 300);
  };

  const getToastBg = (variant: Notification['variant']) => {
    switch (variant) {
      case 'success': return 'success';
      case 'info': return 'info';
      case 'warning': return 'warning';
      case 'danger': return 'danger';
      default: return 'light';
    }
  };

  const getToastIcon = (variant: Notification['variant']) => {
    switch (variant) {
      case 'success': return '✓';
      case 'info': return 'ℹ';
      case 'warning': return '⚠';
      case 'danger': return '✕';
      default: return '•';
    }
  };

  return (
    <ToastContainer 
      position="top-end" 
      className="p-3"
      style={{ zIndex: 1050 }}
    >
      {notifications.map((notification) => (
        <Toast
          key={notification.id}
          show={notification.show}
          onClose={() => dismissNotification(notification.id)}
          bg={getToastBg(notification.variant)}
          autohide={false}
        >
          <Toast.Header>
            <strong className="me-auto">
              <span className="me-2">{getToastIcon(notification.variant)}</span>
              {notification.title}
            </strong>
            <small className="text-muted">
              {notification.timestamp.toLocaleTimeString()}
            </small>
          </Toast.Header>
          <Toast.Body className={notification.variant === 'danger' ? 'text-white' : ''}>
            {notification.message}
          </Toast.Body>
        </Toast>
      ))}
    </ToastContainer>
  );
};

export default LiveNotifications;
