import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import api from '../utils/api'

export default function QuizCard({ quiz, isAdmin = false }) {
  const [myResultId, setMyResultId] = useState(null)
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    if (isAdmin) return
    let isMounted = true
    const checkResult = async () => {
      try {
        setChecking(true)
        const res = await api.get(`/quizzes/${quiz.id}/my-result`)
        if (isMounted && res?.data?.id) {
          setMyResultId(res.data.id)
        }
      } catch (_) {
        // 404 means no completed attempt – ignore
      } finally {
        if (isMounted) setChecking(false)
      }
    }
    checkResult()
    return () => { isMounted = false }
  }, [quiz.id, isAdmin])
  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow p-6 border border-gray-200">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-xl font-bold text-gray-900">{quiz.title}</h3>
        <span className="bg-indigo-100 text-indigo-800 text-xs font-semibold px-3 py-1 rounded-full">
          {quiz.time_limit_minutes} min
        </span>
      </div>

      <p className="text-gray-600 mb-4 line-clamp-2">{quiz.description}</p>

      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
        <span>📝 {quiz.questions?.length || 0} questions</span>
      </div>

      <div className="flex gap-2">
        {isAdmin ? (
          <>
            <Link
              to={`/admin/quiz/edit/${quiz.id}`}
              className="flex-1 bg-indigo-600 text-white text-center py-2 rounded-lg hover:bg-indigo-700 transition font-medium"
            >
              Edit
            </Link>
            <Link
              to={`/admin/quiz/${quiz.id}/results`}
              className="flex-1 bg-green-600 text-white text-center py-2 rounded-lg hover:bg-green-700 transition font-medium"
            >
              View Results
            </Link>
          </>
        ) : myResultId ? (
          <Link
            to={`/results/${myResultId}`}
            className="w-full bg-green-600 text-white text-center py-2 rounded-lg hover:bg-green-700 transition font-medium"
          >
            View Result
          </Link>
        ) : (
          <Link
            to={`/quiz/${quiz.id}`}
            className="w-full bg-indigo-600 text-white text-center py-2 rounded-lg hover:bg-indigo-700 transition font-medium"
            aria-disabled={checking}
          >
            {checking ? 'Checking…' : 'Start Quiz'}
          </Link>
        )}
      </div>
    </div>
  )
}