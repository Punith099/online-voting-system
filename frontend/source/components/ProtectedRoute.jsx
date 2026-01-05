import { Navigate } from 'react-router-dom'

export default function ProtectedRoute({ user, allowedRoles, children }) {
  // Not logged in - redirect to login
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // User role not allowed for this route
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to appropriate dashboard based on role
    return <Navigate to={user.role === 'admin' ? '/admin' : '/dashboard'} replace />
  }

  // User is authorized - render the component
  return children
}