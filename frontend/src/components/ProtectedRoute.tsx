import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/lib/auth';

interface ProtectedRouteProps {
  children: ReactNode;
  requireAuth?: boolean;
}

export function ProtectedRoute({ children, requireAuth = true }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // If loading, show a simple loader
  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Authenticating...</div>;
  }

  // For routes that require authentication
  if (requireAuth && !isAuthenticated) {
    // Store the page they were trying to visit for redirect after login
    const returnTo = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?returnTo=${returnTo}`} replace />;
  }

  // For routes that should only be accessed when NOT authenticated (like login page)
  if (!requireAuth && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}