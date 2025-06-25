import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Header from './components/Layout/Header';
import Footer from './components/Layout/Footer';
import LoadingSpinner from './components/UI/LoadingSpinner';

// Pages
import Home from './pages/Home';
import About from './pages/About';
import FAQ from './pages/FAQ';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';

// Protected Route Component
type User = {
  id: string;
  email: string;
  role: string;
  // add other user properties as needed
};

const ProtectedRoute: React.FC<{ children: React.ReactNode; adminOnly?: boolean }> = ({ 
  children, 
  adminOnly = false 
}) => {
  const { user, isLoading }: { user: User | null, isLoading: boolean } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && user && user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};
// Lazy load components for better performance
const Dashboard = React.lazy(() => import('./pages/user/Dashboard'));
const LoanApplication = React.lazy(() => import('./pages/user/LoanApplication'));
const UserLoans = React.lazy(() => import('./pages/user/UserLoans'));
const AdminDashboard = React.lazy(() => import('./pages/admin/AdminDashboard'));
const AdminApplications = React.lazy(() => import('./pages/admin/AdminApplications'));
const AdminLoans = React.lazy(() => import('./pages/admin/AdminLoans'));

const AppContent: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      <main className="flex-1">
        <React.Suspense fallback={
          <div className="min-h-screen flex items-center justify-center">
            <LoadingSpinner size="lg" />
          </div>
        }>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/faq" element={<FAQ />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected User Routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/apply" element={
              <ProtectedRoute>
                <LoanApplication />
              </ProtectedRoute>
            } />
            <Route path="/loans" element={
              <ProtectedRoute>
                <UserLoans />
              </ProtectedRoute>
            } />

            {/* Admin Routes */}
            {/* Admin Routes */}
            <Route path="/admin" element={
              <ProtectedRoute adminOnly>
                <AdminDashboard />
              </ProtectedRoute>
            } />
            <Route path="/admin/applications" element={
              <ProtectedRoute adminOnly>
                <AdminApplications />
              </ProtectedRoute>
            } />
            <Route path="/admin/loans" element={
              <ProtectedRoute adminOnly>
                <AdminLoans />
              </ProtectedRoute>
            } />
            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </React.Suspense>
      </main>
      <Footer />
    </div>
  );
};
const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
};

export default App;