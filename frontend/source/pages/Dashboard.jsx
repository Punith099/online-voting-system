import { useState, useEffect } from 'react'
import api from '../utils/api'
import QuizCard from '../components/QuizCard'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

export default function Dashboard() {
  const [quizzes, setQuizzes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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

  useEffect(() => {
    fetchQuizzes()
  }, [])

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Available Quizzes
        </h1>
        <p className="text-gray-600">
          Choose a quiz to test your knowledge
        </p>
      </div>

      {loading && <LoadingSpinner message="Loading quizzes..." />}
      
      {error && <ErrorMessage message={error} onRetry={fetchQuizzes} />}

      {!loading && !error && quizzes.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-xl text-gray-600">No quizzes available yet.</p>
          <p className="text-gray-500 mt-2">Check back later!</p>
        </div>
      )}

      {!loading && !error && quizzes.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {quizzes.map((quiz) => (
            <QuizCard key={quiz.id} quiz={quiz} />
          ))}
        </div>
      )}
    </div>
  )
}
