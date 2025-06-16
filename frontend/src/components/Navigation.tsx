import React from 'react';
import { Navbar, Nav, Container, Dropdown } from 'react-bootstrap';
import { LinkContainer } from 'react-router-bootstrap';
import { useAuth } from '../contexts/AuthContext';

const Navigation: React.FC = () => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
      <Container>
        <LinkContainer to="/admin">
          <Navbar.Brand>Kiosk Show Replacement</Navbar.Brand>
        </LinkContainer>
        
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <LinkContainer to="/admin">
              <Nav.Link>Dashboard</Nav.Link>
            </LinkContainer>
            <LinkContainer to="/admin/slideshows">
              <Nav.Link>Slideshows</Nav.Link>
            </LinkContainer>
            <LinkContainer to="/admin/displays">
              <Nav.Link>Displays</Nav.Link>
            </LinkContainer>
          </Nav>
          
          <Nav>
            <Dropdown align="end">
              <Dropdown.Toggle variant="outline-light" id="user-dropdown">
                {user?.username || 'User'}
              </Dropdown.Toggle>
              
              <Dropdown.Menu>
                <Dropdown.ItemText>
                  <div>
                    <div><strong>{user?.username}</strong></div>
                    <div className="text-muted small">
                      {user?.is_admin ? 'Administrator' : 'User'}
                    </div>
                  </div>
                </Dropdown.ItemText>
                <Dropdown.Divider />
                <Dropdown.Item onClick={handleLogout}>
                  Sign Out
                </Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Navigation;
