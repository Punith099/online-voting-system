import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../utils/api'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

export default function Results() {
  const { id } = useParams()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    // Results are returned from submit endpoint, but we'll fetch if needed
    // Try to hydrate from session first; if missing, fetch by attempt id
    const fetchResult = async () => {
      try {
        const response = await api.get(`/results/${id}`)
        setResult(response.data)
        setLoading(false)
      } catch (err) {
        setError('Results not available. Please take the quiz again.')
        setLoading(false)
      }
    }

    // Check if result was passed through navigation state
    const storedResult = sessionStorage.getItem('quiz_result')
    if (storedResult) {
      setResult(JSON.parse(storedResult))
      sessionStorage.removeItem('quiz_result')
      setLoading(false)
    } else {
      fetchResult()
    }
  }, [id])

  if (loading) return <LoadingSpinner message="Loading results..." />
  if (error) return <ErrorMessage message={error} />

  if (!result) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <p className="text-yellow-800">Results not available. Please take the quiz again.</p>
          <Link to="/dashboard" className="text-yellow-900 underline mt-2 inline-block">
            Go to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  const percentage = result.score
  const passed = percentage >= 50
  const marks = result.correct_answers
  const total = result.total_questions

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Score Card */}
      <div className={`rounded-lg shadow-xl p-8 mb-6 text-center ${
        passed ? 'bg-gradient-to-br from-green-400 to-green-600' : 'bg-gradient-to-br from-red-400 to-red-600'
      } text-white`}>
        <h1 className="text-4xl font-bold mb-4">
          {passed ? '🎉 Great Job!' : '📚 Keep Practicing!'}
        </h1>
        <div className="text-7xl font-bold mb-2">{percentage.toFixed(1)}%</div>
        <p className="text-xl mb-1">
          {marks} out of {total} correct
        </p>
        <p className="text-lg opacity-90 mb-1">Score: {marks} / {total}</p>
        <p className="text-lg opacity-90">{result.quiz_title}</p>
      </div>

      {/* Detailed Results */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Question Breakdown</h2>

        <div className="space-y-6">
          {result.question_results && result.question_results.map((qr, index) => (
            <div key={index} className={`p-5 rounded-lg border-2 ${
              qr.is_correct ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
            }`}>
              <div className="flex items-start mb-3">
                <span className={`text-2xl mr-3 ${qr.is_correct ? 'text-green-600' : 'text-red-600'}`}>
                  {qr.is_correct ? '✓' : '✗'}
                </span>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-2">
                    Question {index + 1}: {qr.question_text}
                  </h3>
                  
                  {!qr.is_correct && (
                    <div className="space-y-2">
                      <div className="text-red-700">
                        <strong>Your answer:</strong> Option {qr.chosen_index + 1}
                      </div>
                      <div className="text-green-700">
                        <strong>Correct answer:</strong> Option {qr.correct_index + 1}
                      </div>
                    </div>
                  )}
                  
                  {qr.is_correct && (
                    <div className="text-green-700">
                      <strong>Your answer was correct!</strong> Option {qr.chosen_index + 1}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4 justify-center">
        <Link
          to="/dashboard"
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium"
        >
          Back to Dashboard
        </Link>
        <Link
          to={`/quiz/${result.quiz_id}`}
          className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-medium"
        >
          Retake Quiz
        </Link>
      </div>
    </div>
  )
}
