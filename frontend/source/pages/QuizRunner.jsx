import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../utils/api'
import Timer from '../components/Timer'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

export default function QuizRunner() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [quiz, setQuiz] = useState(null)
  const [attemptId, setAttemptId] = useState(null)
  const [endTime, setEndTime] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    startQuiz()
  }, [id])

  const startQuiz = async () => {
    try {
      setLoading(true)
      setError('')

      // First start the attempt to avoid a race condition
      let startResponse = await api.post(`/quizzes/${id}/start`)
      if (!startResponse?.data?.attempt_id) {
        throw new Error('Invalid start response from server')
      }
      setAttemptId(startResponse.data.attempt_id)

      // Fetch quiz details
      const quizResponse = await api.get(`/quizzes/${id}`)
      if (!quizResponse?.data) {
        throw new Error('Invalid quiz response from server')
      }
      setQuiz(quizResponse.data)

      // Calculate end time in UTC, but handle case where the returned attempt is already expired
      const startTimeRaw = startResponse.data.start_time || ''
      const startTimeIso = startTimeRaw.endsWith('Z') ? startTimeRaw : `${startTimeRaw}Z`
      let parsedStart = new Date(startTimeIso)
      if (isNaN(parsedStart.getTime())) {
        // Fallback: try parsing without Z
        parsedStart = new Date(startResponse.data.start_time)
      }
      const timeLimitMinutes = startResponse.data.time_limit_minutes ?? quizResponse.data.time_limit_minutes
      const timeLimitMs = Math.max(1, Number(timeLimitMinutes || 0)) * 60000
      let remainingMs = parsedStart.getTime() + timeLimitMs - Date.now()

      // If remainingMs is zero or negative the attempt has already expired on the server side.
      // Retry starting once to allow the backend to mark expired attempts closed and create a fresh one.
      if (remainingMs <= 0) {
        console.debug('Attempt returned by /start already expired; retrying start to get a fresh attempt')
        startResponse = await api.post(`/quizzes/${id}/start`)
        setAttemptId(startResponse.data.attempt_id)

        const startTimeRaw2 = startResponse.data.start_time || ''
        const startTimeIso2 = startTimeRaw2.endsWith('Z') ? startTimeRaw2 : `${startTimeRaw2}Z`
        let startTime2 = new Date(startTimeIso2)
        if (isNaN(startTime2.getTime())) {
          startTime2 = new Date(startResponse.data.start_time)
        }
        const tlm2 = Math.max(1, Number(startResponse.data.time_limit_minutes || timeLimitMinutes || 1)) * 60000
        remainingMs = startTime2.getTime() + tlm2 - Date.now()
        setEndTime(new Date(startTime2.getTime() + tlm2).toISOString())
      } else {
        setEndTime(new Date(parsedStart.getTime() + timeLimitMs).toISOString())
      }

      // Initialize answers object
      const initialAnswers = {}
      const questions = Array.isArray(quizResponse.data.questions) ? quizResponse.data.questions : []
      for (const q of questions) {
        if (q && q.id) initialAnswers[q.id] = null
      }
      setAnswers(initialAnswers)
    } catch (err) {
      console.error('Error starting quiz:', err)
      setError(err.response?.data?.detail || 'Failed to start quiz. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleAnswer = (questionId, optionIndex) => {
    setAnswers({
      ...answers,
      [questionId]: optionIndex
    })
  }

    const handleSubmit = async () => {
      // Check if all questions are answered
      const unansweredQuestions = quiz.questions.filter(q => answers[q.id] === null)
      if (unansweredQuestions.length > 0) {
        setError(`Please answer all questions before submitting. ${unansweredQuestions.length} question(s) remaining.`)
        return
      }

      if (!confirm('Are you sure you want to submit? You cannot change your answers after submission.')) {
        return
      }

      setSubmitting(true)
      setError('')

      try {
        // Format answers for submission (now guaranteed to be all questions)
        const formattedAnswers = Object.entries(answers).map(([question_id, chosen_index]) => ({
          question_id,
          chosen_index
        }))

        const response = await api.post(`/quizzes/${id}/submit`, {
          attempt_id: attemptId,
          answers: formattedAnswers
        })

        // Persist result so Results page can load it
        sessionStorage.setItem('quiz_result', JSON.stringify(response.data))
        // Navigate to results page
        navigate(`/results/${response.data.id}`)
      } catch (err) {
        console.error('Quiz submission error:', err)
        // Get detailed error message from the API response if available
        const errorMessage = err.response?.data?.detail || 'Failed to submit quiz. Please try again.'
        setError(errorMessage)
        setSubmitting(false)
      }
    }

  const handleTimeUp = async () => {
    // If already submitting or submitted, do nothing
    if (submitting) return

    try {
      setSubmitting(true)
      setError('')

      // Show alert once
      alert('Time is up! Submitting your answers...')

      // Format answers for submission - send whatever we have
      const formattedAnswers = Object.entries(answers)
        .filter(([_, value]) => value !== null)
        .map(([question_id, chosen_index]) => ({
          question_id,
          chosen_index
        }))

      // Submit without confirmation since time is up
      const response = await api.post(`/quizzes/${id}/submit`, {
        attempt_id: attemptId,
        answers: formattedAnswers
      })

      // Persist result so Results page can load it
      sessionStorage.setItem('quiz_result', JSON.stringify(response.data))
      // Only navigate if submission was successful
      navigate(`/results/${response.data.id}`)
    } catch (err) {
      console.error('Auto-submission error:', err)
      const errorMessage = err.response?.data?.detail || 'Failed to auto-submit quiz.'
      setError(errorMessage)
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <LoadingSpinner message="Starting quiz..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-8 px-4">
        <ErrorMessage message={error} onRetry={startQuiz} />
      </div>
    )
  }

  if (!quiz) return null

  const currentQ = quiz.questions[currentQuestion]
  const progress = ((currentQuestion + 1) / quiz.questions.length) * 100

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {endTime && <Timer endTime={endTime} onTimeUp={handleTimeUp} />}

      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{quiz.title}</h1>
        <p className="text-gray-600 mb-4">{quiz.description}</p>

        {/* Progress bar */}
        <div className="mb-2">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Question {currentQuestion + 1} of {quiz.questions.length}</span>
            <span>{Math.round(progress)}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Question */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">
          {currentQ.text}
        </h2>

        <div className="space-y-3">
          {currentQ.options.map((option, index) => (
            <button
              key={index}
              onClick={() => handleAnswer(currentQ.id, index)}
              className={`w-full text-left p-4 rounded-lg border-2 transition ${
                answers[currentQ.id] === index
                  ? 'border-indigo-600 bg-indigo-50'
                  : 'border-gray-300 hover:border-indigo-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center">
                <div className={`w-6 h-6 rounded-full border-2 mr-3 flex items-center justify-center ${
                  answers[currentQ.id] === index
                    ? 'border-indigo-600 bg-indigo-600'
                    : 'border-gray-400'
                }`}>
                  {answers[currentQ.id] === index && (
                    <span className="text-white text-sm">✓</span>
                  )}
                </div>
                <span className="text-gray-900">{option}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center">
        <button
          onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
          disabled={currentQuestion === 0}
          className="px-6 py-3 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
        >
          Previous
        </button>

        <div className="text-sm text-gray-600">
          {Object.values(answers).filter(a => a !== null).length} / {quiz.questions.length} answered
        </div>

        {currentQuestion < quiz.questions.length - 1 ? (
          <button
            onClick={() => setCurrentQuestion(currentQuestion + 1)}
            className="px-6 py-3 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition font-medium"
          >
            Next
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="px-6 py-3 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition font-medium"
          >
            {submitting ? 'Submitting...' : 'Submit Quiz'}
          </button>
        )}
      </div>

      {/* Question navigation dots */}
      <div className="mt-6 flex flex-wrap gap-2 justify-center">
        {quiz.questions.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentQuestion(index)}
            className={`w-10 h-10 rounded-full font-medium transition ${
              index === currentQuestion
                ? 'bg-indigo-600 text-white'
                : answers[quiz.questions[index].id] !== null
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
            }`}
          >
            {index + 1}
          </button>
        ))}
      </div>
    </div>
  )
}