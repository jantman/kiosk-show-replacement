import React from 'react';
import { Outlet } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import Navigation from './Navigation';
import LiveNotifications from './LiveNotifications';
import { SSEProvider, useSSEContext } from '../hooks/useSSE';

const AdminLayoutContent: React.FC = () => {
  const { connectionState } = useSSEContext();
  
  const getStatusColor = () => {
    switch (connectionState) {
      case 'connected': return 'text-success';
      case 'connecting': return 'text-warning';
      case 'error': return 'text-danger';
      case 'disconnected': return 'text-muted';
      default: return 'text-muted';
    }
  };

  const getStatusIcon = () => {
    switch (connectionState) {
      case 'connected': return '●';
      case 'connecting': return '◐';
      case 'error': return '✕';
      case 'disconnected': return '○';
      default: return '○';
    }
  };
  
  return (
    <div className="min-vh-100 bg-light">
      <Navigation />
      <Container>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <div></div>
          <div className={`text-muted small ${getStatusColor()}`}>
            <span className="me-1">{getStatusIcon()}</span>
            SSE: {connectionState === 'connected' ? 'Live Updates' : connectionState}
          </div>
        </div>
        <Outlet />
      </Container>
      <LiveNotifications />
    </div>
  );
};

const AdminLayout: React.FC = () => {
  return (
    <SSEProvider>
      <AdminLayoutContent />
    </SSEProvider>
  );
};

export default AdminLayout;
