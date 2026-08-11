import { Link } from 'react-router-dom'

// Placeholder - would fetch from API in production
const MOCK_HISTORY = [
  { id: '1', destination: 'Tokyo', days: 3, createdAt: '2024-03-10' },
  { id: '2', destination: 'Osaka', days: 5, createdAt: '2024-03-08' },
]

export default function History() {
  return (
    <div className="history-page">
      <header className="page-header">
        <Link to="/" className="back-link">← Back to Home</Link>
        <h1>📋 Itinerary History</h1>
      </header>

      <main className="container">
        {MOCK_HISTORY.length === 0 ? (
          <div className="card" style={{ textAlign: 'center' }}>
            <p>No itineraries yet. Create your first one!</p>
            <Link to="/" className="btn btn-primary" style={{ marginTop: '1rem', display: 'inline-block' }}>
              Create Itinerary
            </Link>
          </div>
        ) : (
          <div className="history-list">
            {MOCK_HISTORY.map(item => (
              <Link to={`/itinerary/${item.id}`} key={item.id} className="history-item card">
                <div className="item-info">
                  <h3>🗾 {item.destination}</h3>
                  <p>{item.days} days</p>
                </div>
                <div className="item-meta">
                  <span>Created: {item.createdAt}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
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
        .history-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .history-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          text-decoration: none;
          color: inherit;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .history-item:hover {
          transform: translateY(-2px);
          box-shadow: var(--shadow-lg);
        }
        .item-info h3 {
          margin: 0 0 0.25rem 0;
        }
        .item-info p {
          margin: 0;
          color: var(--color-text-secondary);
        }
        .item-meta {
          color: var(--color-text-secondary);
          font-size: 0.875rem;
        }
        .container {
          max-width: 800px;
          margin: 0 auto;
          padding: 2rem 1rem;
        }
      `}</style>
    </div>
  )
}
