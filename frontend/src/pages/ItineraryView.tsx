import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import ItineraryViewComponent from '../components/ItineraryView'
import { itineraryApi, ItineraryResponse } from '../api'

export default function ItineraryViewPage() {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<ItineraryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return

    const fetchItinerary = async () => {
      try {
        const response = await itineraryApi.get(id)
        setData(response)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load itinerary')
      } finally {
        setLoading(false)
      }
    }

    fetchItinerary()
  }, [id])

  if (loading) {
    return (
      <div className="loading-page">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading itinerary...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="error-page">
        <div className="card" style={{ textAlign: 'center' }}>
          <h2>❌ Error</h2>
          <p>{error || 'Itinerary not found'}</p>
          <Link to="/" className="btn btn-primary" style={{ marginTop: '1rem', display: 'inline-block' }}>
            Go Home
          </Link>
        </div>
      </div>
    )
  }

  if (data.status === 'pending') {
    return (
      <div className="pending-page">
        <div className="card" style={{ textAlign: 'center' }}>
          <h2>⏳ Generating Itinerary</h2>
          <p>Your AI-powered itinerary is being created...</p>
          <p className="note">This may take a few moments.</p>
          <Link to="/" className="btn btn-primary" style={{ marginTop: '1rem', display: 'inline-block' }}>
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  // For demo, show placeholder itinerary
  const placeholderDays = [
    {
      date: '2024-03-15',
      places: [
        {
          id: '1',
          name: 'Senso-ji Temple',
          category: 'attraction',
          subcategory: 'temple',
          cost_estimate: 0,
          duration_hours: 2,
          rating: 4.7,
          description: "Tokyo's oldest temple",
        },
        {
          id: '2',
          name: 'Tokyo Skytree',
          category: 'attraction',
          subcategory: 'tower',
          cost_estimate: 3100,
          duration_hours: 2.5,
          rating: 4.5,
          description: 'Tallest tower in Japan',
        },
      ],
      total_cost: 3100,
      total_hours: 4.5,
      travel_time_minutes: 30,
    },
  ]

  return (
    <div className="itinerary-page">
      <header className="page-header">
        <Link to="/" className="back-link">← Back to Home</Link>
        <h1>🗾 {data.destination} Itinerary</h1>
      </header>

      <main className="container">
        <ItineraryViewComponent
          days={placeholderDays}
          totalCost={3100}
          totalHours={4.5}
          constraintsSatisfied={true}
          violations={[]}
        />
      </main>

      <style>{`
        .page-header {
          padding: 1.5rem 1rem;
          background: var(--color-card);
          border-bottom: 1px solid #e2e8f0;
        }
        .page-header h1 {
          margin: 0;
        }
        .back-link {
          display: inline-block;
          margin-bottom: 0.5rem;
          color: var(--color-primary);
          text-decoration: none;
        }
        .back-link:hover {
          text-decoration: underline;
        }
        .loading-page, .error-page, .pending-page {
          min-height: 60vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
        }
        .loading {
          text-align: center;
        }
        .loading .spinner {
          margin: 0 auto 1rem;
        }
        .note {
          color: var(--color-text-secondary);
          font-size: 0.875rem;
        }
        .container {
          padding-top: 2rem;
          padding-bottom: 2rem;
        }
      `}</style>
    </div>
  )
}
