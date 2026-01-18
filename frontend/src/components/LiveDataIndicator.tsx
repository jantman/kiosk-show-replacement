/**
 * LiveDataIndicator - Component to show live data updates
 * 
 * Displays a small indicator next to data that can be updated in real-time
 * via SSE events.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Badge } from 'react-bootstrap';
import { useSSEContext, DisplayEventData, SlideshowEventData } from '../hooks/useSSE.tsx';

interface LiveDataIndicatorProps {
  /** Type of data being monitored (display, slideshow, etc.) */
  dataType: 'display' | 'slideshow' | 'assignment';
  /** ID of the specific data item */
  dataId?: number | string;
  /** Optional className for styling */
  className?: string;
}

const LiveDataIndicator: React.FC<LiveDataIndicatorProps> = ({ 
  dataType, 
  dataId, 
  className = '' 
}) => {
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const { addEventListener, connectionState } = useSSEContext();

  const handleUpdate = useCallback(() => {
    setLastUpdate(new Date());
    setIsUpdating(true);

    // Reset updating state after animation
    setTimeout(() => {
      setIsUpdating(false);
    }, 1000);
  }, []);

  useEffect(() => {
    const eventHandlers: Array<() => void> = [];

    // Register event handlers based on data type
    switch (dataType) {
      case 'display':
        eventHandlers.push(
          addEventListener('display.status_changed', (event) => {
            const data = event.data as DisplayEventData;
            if (!dataId || data.display_id === dataId || data.display_name === dataId) {
              handleUpdate();
            }
          }),
          addEventListener('display.configuration_changed', (event) => {
            const data = event.data as DisplayEventData;
            if (!dataId || data.display_id === dataId || data.display_name === dataId) {
              handleUpdate();
            }
          }),
          addEventListener('display.assignment_changed', (event) => {
            const data = event.data as DisplayEventData;
            if (!dataId || data.display_id === dataId || data.display_name === dataId) {
              handleUpdate();
            }
          })
        );
        break;

      case 'slideshow':
        eventHandlers.push(
          addEventListener('slideshow.updated', (event) => {
            const data = event.data as SlideshowEventData;
            if (!dataId || data.slideshow_id === dataId) {
              handleUpdate();
            }
          }),
          addEventListener('slideshow.created', (event) => {
            const data = event.data as SlideshowEventData;
            if (!dataId || data.slideshow_id === dataId) {
              handleUpdate();
            }
          })
        );
        break;

      case 'assignment':
        eventHandlers.push(
          addEventListener('display.assignment_changed', () => {
            handleUpdate();
          })
        );
        break;
    }

    return () => {
      eventHandlers.forEach(cleanup => cleanup());
    };
  }, [dataType, dataId, addEventListener, handleUpdate]);

  const getStatusIcon = () => {
    if (connectionState !== 'connected') {
      return '○'; // Disconnected
    }
    
    if (isUpdating) {
      return '●'; // Updating
    }
    
    if (lastUpdate) {
      return '◉'; // Has updates
    }
    
    return '◐'; // Connected, no updates yet
  };

  const getStatusColor = () => {
    if (connectionState !== 'connected') {
      return 'text-muted';
    }
    
    if (isUpdating) {
      return 'text-success';
    }
    
    if (lastUpdate) {
      return 'text-info';
    }
    
    return 'text-warning';
  };

  const getTooltipText = () => {
    if (connectionState !== 'connected') {
      return 'Live updates disconnected';
    }
    
    if (isUpdating) {
      return 'Updating...';
    }
    
    if (lastUpdate) {
      return `Last updated: ${lastUpdate.toLocaleTimeString()}`;
    }
    
    return 'Live updates active';
  };

  if (connectionState === 'disconnected') {
    return null; // Don't show indicator when completely disconnected
  }

  return (
    <Badge 
      bg="light" 
      text="dark"
      className={`live-data-indicator ${className} ${isUpdating ? 'updating' : ''}`}
      style={{ 
        fontSize: '0.7rem',
        animation: isUpdating ? 'pulse 0.5s ease-in-out' : undefined
      }}
      title={getTooltipText()}
    >
      <span className={getStatusColor()}>{getStatusIcon()}</span>
      <span className="ms-1 small">Live</span>
      <style>{`
        .live-data-indicator.updating {
          transform: scale(1.1);
          transition: transform 0.3s ease;
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </Badge>
  );
};

export default LiveDataIndicator;
