import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PreferenceForm from '../components/PreferenceForm'
import { Preferences, itineraryApi } from '../api'

export default function Home() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (preferences: Preferences) => {
    setLoading(true)
    setError(null)

    try {
      const response = await itineraryApi.create({
        destination: preferences.destination,
        days: preferences.days,
        people: preferences.people,
        budget: preferences.budget,
        preferences: {
          style: preferences.style,
          mobility: preferences.mobility,
        },
      })

      if (response.id) {
        navigate(`/itinerary/${response.id}`)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create itinerary')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="home-page">
      <header className="hero">
        <h1>🗾 Travel Planner</h1>
        <p>AI-powered itinerary generator for Japan</p>
      </header>

      <main className="main-content">
        <div className="card">
          <h2>Plan Your Trip</h2>
          <p className="subtitle">Enter your preferences and let AI create your perfect itinerary</p>

          {error && <div className="error-message">{error}</div>}

          <PreferenceForm onSubmit={handleSubmit} loading={loading} />
        </div>

        <div className="features">
          <div className="feature">
            <span className="feature-icon">🤖</span>
            <h3>AI-Powered</h3>
            <p>Smart recommendations based on your preferences</p>
          </div>
          <div className="feature">
            <span className="feature-icon">📍</span>
            <h3>Local Insights</h3>
            <p>Handpicked places and hidden gems</p>
          </div>
          <div className="feature">
            <span className="feature-icon">💰</span>
            <h3>Budget Smart</h3>
            <p>Stay within your budget constraints</p>
          </div>
        </div>
      </main>

      <style>{`
        .home-page {
          min-height: 100vh;
        }
        .hero {
          text-align: center;
          padding: 3rem 1rem;
          background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
          color: white;
        }
        .hero h1 {
          font-size: 2.5rem;
          margin-bottom: 0.5rem;
        }
        .hero p {
          font-size: 1.25rem;
          opacity: 0.9;
        }
        .main-content {
          max-width: 600px;
          margin: -2rem auto 2rem;
          padding: 0 1rem;
        }
        .main-content .card {
          text-align: center;
        }
        .main-content h2 {
          margin-bottom: 0.5rem;
          color: var(--color-text);
        }
        .subtitle {
          color: var(--color-text-secondary);
          margin-bottom: 1.5rem;
        }
        .error-message {
          background: #fef2f2;
          border: 1px solid #fca5a5;
          color: #dc2626;
          padding: 0.75rem;
          border-radius: var(--border-radius);
          margin-bottom: 1rem;
        }
        .features {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1rem;
          margin-top: 2rem;
          text-align: center;
        }
        .feature {
          padding: 1rem;
        }
        .feature-icon {
          font-size: 2rem;
          display: block;
          margin-bottom: 0.5rem;
        }
        .feature h3 {
          font-size: 1rem;
          margin-bottom: 0.25rem;
        }
        .feature p {
          font-size: 0.875rem;
          color: var(--color-text-secondary);
        }
        @media (max-width: 500px) {
          .features {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  )
}
