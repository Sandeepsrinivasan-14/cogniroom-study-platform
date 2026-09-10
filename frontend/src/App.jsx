import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';

// Lazy load heavier pages for performance
const RoomView = lazy(() => import('./pages/RoomView'));
const Analytics = lazy(() => import('./pages/Analytics'));
const RoomAnalytics = lazy(() => import('./pages/RoomAnalytics'));
const MentorDash = lazy(() => import('./pages/MentorDash'));
const AdminDash = lazy(() => import('./pages/AdminDash'));
const Profile = lazy(() => import('./pages/Profile'));

const LoadingFallback = () => (
  <div className="flex-center" style={{ height: '100%', minHeight: '400px' }}>
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '1rem',
    }}>
      <div style={{
        width: '44px',
        height: '44px',
        border: '3px solid var(--glass-border)',
        borderTopColor: 'var(--accent-cyan)',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading...</span>
    </div>
  </div>
);

const ProtectedRoute = ({ children, roles = [] }) => {
  const { isAuthenticated, loading, user } = useAuth();

  if (loading) return <LoadingFallback />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (roles.length > 0 && !roles.includes(user?.role)) return <Navigate to="/dashboard" replace />;

  return children;
};

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="room/:roomId" element={<RoomView />} />
            <Route path="room/:roomId/analytics" element={<RoomAnalytics />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="profile" element={<Profile />} />
            
            {/* Role specific routes */}
            <Route 
              path="mentor" 
              element={<ProtectedRoute roles={['mentor', 'admin']}><MentorDash /></ProtectedRoute>} 
            />
            <Route 
              path="admin" 
              element={<ProtectedRoute roles={['admin']}><AdminDash /></ProtectedRoute>} 
            />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
