// ============================================================================
// Authentication utilities for frontend
// ============================================================================

/**
 * Store authentication token and user info in localStorage
 * Called after successful login/signup
 */
export const setAuth = (token, user) => {
  localStorage.setItem('token', token)
  localStorage.setItem('user', JSON.stringify(user))
}

/**
 * Get authentication token from localStorage
 * Used to attach to API requests
 */
export const getToken = () => {
  return localStorage.getItem('token')
}

/**
 * Get current user info from localStorage
 * Returns null if not logged in
 */
export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user')
  if (!userStr) return null
  
  try {
    return JSON.parse(userStr)
  } catch (error) {
    return null
  }
}

/**
 * Clear authentication data
 * Called on logout
 */
export const clearAuth = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
  return !!getToken()
}
