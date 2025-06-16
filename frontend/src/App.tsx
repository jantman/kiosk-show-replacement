import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AdminLayout from './components/AdminLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

// Import Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected admin routes */}
          <Route path="/admin" element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }>
            {/* Dashboard */}
            <Route index element={<Dashboard />} />
            
            {/* Placeholder routes for future milestones */}
            <Route path="slideshows" element={
              <div className="text-center py-5">
                <h3>Slideshow Management</h3>
                <p className="text-muted">Coming in Milestone 9</p>
              </div>
            } />
            
            <Route path="displays" element={
              <div className="text-center py-5">
                <h3>Display Management</h3>
                <p className="text-muted">Coming in Milestone 10</p>
              </div>
            } />
          </Route>
          
          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/admin" replace />} />
          
          {/* Catch all route */}
          <Route path="*" element={
            <div className="text-center py-5">
              <h1>404</h1>
              <p>Page not found</p>
            </div>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
