/**
 * ProtectedRoute — wraps routes that require authentication.
 * Redirects to /login if no valid token is found in the auth store.
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export default function ProtectedRoute() {
  const { accessToken } = useAuthStore();
  const location = useLocation();

  if (!accessToken) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
