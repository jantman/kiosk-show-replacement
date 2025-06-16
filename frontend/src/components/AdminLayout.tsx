import React from 'react';
import { Outlet } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import Navigation from './Navigation';

const AdminLayout: React.FC = () => {
  return (
    <div className="min-vh-100 bg-light">
      <Navigation />
      <Container>
        <Outlet />
      </Container>
    </div>
  );
};

export default AdminLayout;
