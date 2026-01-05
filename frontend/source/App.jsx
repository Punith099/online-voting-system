import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import AdminDashboard from './pages/AdminDashboard'
import QuizRunner from './pages/QuizRunner'
import Results from './pages/Results'
import CreateQuiz from './pages/CreateQuiz'
import EditQuiz from './pages/EditQuiz'
import QuizResults from './pages/QuizResults'
import ProtectedRoute from './components/ProtectedRoute'
import { getCurrentUser } from './utils/auth'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in on mount
    const currentUser = getCurrentUser()
    setUser(currentUser)
    setLoading(false)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar user={user} setUser={setUser} />
        <Routes>
          <Route path="/login" element={
            user ? <Navigate to={user.role === 'admin' ? '/admin' : '/dashboard'} /> : <Login setUser={setUser} />
          } />
          <Route path="/signup" element={
            user ? <Navigate to={user.role === 'admin' ? '/admin' : '/dashboard'} /> : <Signup setUser={setUser} />
          } />
          
          {/* Student routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute user={user} allowedRoles={['student']}>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/quiz/:id" element={
            <ProtectedRoute user={user} allowedRoles={['student']}>
              <QuizRunner />
            </ProtectedRoute>
          } />
          <Route path="/results/:id" element={
            <ProtectedRoute user={user} allowedRoles={['student']}>
              <Results />
            </ProtectedRoute>
          } />
          
          {/* Admin routes */}
          <Route path="/admin" element={
            <ProtectedRoute user={user} allowedRoles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          } />
          <Route path="/admin/quiz/create" element={
            <ProtectedRoute user={user} allowedRoles={['admin']}>
              <CreateQuiz />
            </ProtectedRoute>
          } />
          <Route path="/admin/quiz/edit/:id" element={
            <ProtectedRoute user={user} allowedRoles={['admin']}>
              <EditQuiz />
            </ProtectedRoute>
          } />
          <Route path="/admin/quiz/:id/results" element={
            <ProtectedRoute user={user} allowedRoles={['admin']}>
              <QuizResults />
            </ProtectedRoute>
          } />
          
          {/* Default redirect */}
          <Route path="/" element={
            <Navigate to={user ? (user.role === 'admin' ? '/admin' : '/dashboard') : '/login'} />
          } />
        </Routes>
      </div>
    </Router>
  )
}

export default App