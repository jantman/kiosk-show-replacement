import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AdminLayout from './components/AdminLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Slideshows from './pages/Slideshows';
import SlideshowForm from './pages/SlideshowForm';
import SlideshowDetail from './pages/SlideshowDetail';
import Displays from './pages/Displays';
import DisplayDetail from './pages/DisplayDetail';
import AssignmentHistory from './pages/AssignmentHistory';
import SystemMonitoring from './pages/SystemMonitoring';

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
            
            {/* Slideshow Management */}
            <Route path="slideshows" element={<Slideshows />} />
            <Route path="slideshows/new" element={<SlideshowForm />} />
            <Route path="slideshows/:id" element={<SlideshowDetail />} />
            <Route path="slideshows/:id/edit" element={<SlideshowForm />} />
            
            {/* Display Management */}
            <Route path="displays" element={<Displays />} />
            <Route path="displays/:id" element={<DisplayDetail />} />
            
            {/* Assignment History */}
            <Route path="assignment-history" element={<AssignmentHistory />} />
            
            {/* System Monitoring */}
            <Route path="monitoring" element={<SystemMonitoring />} />
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
