import { Link, useNavigate } from 'react-router-dom'
import { clearAuth } from '../utils/auth'

export default function Navbar({ user, setUser }) {
  const navigate = useNavigate()

  const handleLogout = () => {
    clearAuth()
    setUser(null)
    navigate('/login')
  }

  return (
    <nav className="bg-indigo-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Brand */}
          <Link to="/" className="text-2xl font-bold hover:text-indigo-200 transition">
            QuizApp
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-6">
            {user ? (
              <>
                {user.role === 'student' && (
                  <Link 
                    to="/dashboard" 
                    className="hover:text-indigo-200 transition font-medium"
                  >
                    My Quizzes
                  </Link>
                )}
                {user.role === 'admin' && (
                  <>
                    <Link 
                      to="/admin" 
                      className="hover:text-indigo-200 transition font-medium"
                    >
                      Dashboard
                    </Link>
                    <Link 
                      to="/admin/quiz/create" 
                      className="hover:text-indigo-200 transition font-medium"
                    >
                      Create Quiz
                    </Link>
                  </>
                )}
                
                {/* User info and logout */}
                <div className="flex items-center space-x-4 border-l border-indigo-400 pl-6">
                  <span className="text-sm">
                    {user.name} <span className="text-indigo-200">({user.role})</span>
                  </span>
                  <button
                    onClick={handleLogout}
                    className="bg-indigo-700 hover:bg-indigo-800 px-4 py-2 rounded-lg transition font-medium"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link 
                  to="/login" 
                  className="hover:text-indigo-200 transition font-medium"
                >
                  Login
                </Link>
                <Link 
                  to="/signup" 
                  className="bg-indigo-700 hover:bg-indigo-800 px-4 py-2 rounded-lg transition font-medium"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

