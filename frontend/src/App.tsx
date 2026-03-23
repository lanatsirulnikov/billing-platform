import { useEffect, useState } from 'react'
import './App.css'

type HealthResponse = {
  status: string
}

function App() {
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL

    fetch(`${baseUrl}/health`)
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`)
        }
        return (await res.json()) as HealthResponse
      })
      .then((data) => {
        setStatus(data.status)
      })
      .catch((err: Error) => {
        setError(err.message)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  return (
    <main>
      <h1>Billing Platform</h1>
      {loading && <p>Loading backend health...</p>}
      {!loading && !error && <p>Backend health status: {status}</p>}
      {!loading && error && <p style={{ color: 'red' }}>Error: {error}</p>}
    </main>
  )
}

export default App