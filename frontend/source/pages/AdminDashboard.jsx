import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../utils/api'
import QuizCard from '../components/QuizCard'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

export default function AdminDashboard() {
  const [quizzes, setQuizzes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleteLoading, setDeleteLoading] = useState(null)

  const fetchQuizzes = async () => {
    try {
      setLoading(true)
      setError('')
      const response = await api.get('/quizzes')
      setQuizzes(response.data)
    } catch (err) {
      setError('Failed to load quizzes. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (quizId) => {
    if (!confirm('Are you sure you want to delete this quiz? This action cannot be undone.')) {
      return
    }

    try {
      setDeleteLoading(quizId)
      await api.delete(`/quizzes/${quizId}`)
      setQuizzes(quizzes.filter(q => q.id !== quizId))
    } catch (err) {
      alert('Failed to delete quiz. Please try again.')
    } finally {
      setDeleteLoading(null)
    }
  }

  useEffect(() => {
    fetchQuizzes()
  }, [])

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Quiz Management
          </h1>
          <p className="text-gray-600">
            Create and manage your quizzes
          </p>
        </div>
        <Link
          to="/admin/quiz/create"
          className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition font-medium flex items-center gap-2"
        >
          <span className="text-xl">+</span> Create New Quiz
        </Link>
      </div>

      {loading && <LoadingSpinner message="Loading quizzes..." />}
      
      {error && <ErrorMessage message={error} onRetry={fetchQuizzes} />}

      {!loading && !error && quizzes.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-xl text-gray-600 mb-4">No quizzes created yet.</p>
          <Link
            to="/admin/quiz/create"
            className="inline-block bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition"
          >
            Create Your First Quiz
          </Link>
        </div>
      )}

      {!loading && !error && quizzes.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {quizzes.map((quiz) => (
            <div key={quiz.id} className="relative">
              <QuizCard quiz={quiz} isAdmin={true} />
              <button
                onClick={() => handleDelete(quiz.id)}
                disabled={deleteLoading === quiz.id}
                className="absolute top-2 right-2 bg-red-600 text-white px-3 py-1 rounded-lg hover:bg-red-700 transition text-sm font-medium disabled:opacity-50"
              >
                {deleteLoading === quiz.id ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
