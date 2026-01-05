import { useEffect, useState, useRef } from 'react'

export default function Timer({ endTime, onTimeUp }) {
  const [timeLeft, setTimeLeft] = useState(0)
  const timeoutRef = useRef(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    // Clear any existing timers
    if (intervalRef.current) clearInterval(intervalRef.current)
    if (timeoutRef.current) clearTimeout(timeoutRef.current)

    // Calculate initial time left, ensuring UTC handling
    const calculateTimeLeft = () => {
      const now = Date.now()
      const endTimeStr = endTime.endsWith('Z') ? endTime : endTime + 'Z'
      const end = new Date(endTimeStr).getTime()
      return Math.max(0, end - now)
    }

    // Initial calculation
    const initialTimeLeft = calculateTimeLeft()
    setTimeLeft(Math.floor(initialTimeLeft / 1000))

    // Set up exact timeout for time up
    if (initialTimeLeft > 0) {
      timeoutRef.current = setTimeout(() => {
        setTimeLeft(0)
        if (intervalRef.current) clearInterval(intervalRef.current)
        onTimeUp()
      }, initialTimeLeft)

      // Update display every second
      intervalRef.current = setInterval(() => {
        const remaining = calculateTimeLeft()
        setTimeLeft(Math.floor(remaining / 1000))
      }, 1000)
    }

    // Cleanup function
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [endTime, onTimeUp])

  // Format time as MM:SS
  const minutes = Math.floor(timeLeft / 60)
  const seconds = timeLeft % 60

  // Determine color based on time remaining
  let colorClass = 'bg-green-100 text-green-800'
  if (minutes === 0 && seconds <= 30) {
    colorClass = 'bg-red-100 text-red-800 animate-pulse'
  } else if (minutes < 2) {
    colorClass = 'bg-yellow-100 text-yellow-800'
  }

  return (
    <div className={`fixed top-20 right-4 ${colorClass} px-6 py-3 rounded-lg shadow-lg font-mono text-2xl font-bold z-50`}>
      ⏱️ {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
    </div>
  )
}
