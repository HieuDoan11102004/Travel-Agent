import { Place } from '../api'

interface PlaceCardProps {
  place: Place
}

const CATEGORY_ICONS: Record<string, string> = {
  attraction: '🏛️',
  restaurant: '🍽️',
  hotel: '🏨',
  shopping: '🛍️',
  transport: '🚇',
}

export default function PlaceCard({ place }: PlaceCardProps) {
  return (
    <div className="place-card">
      <div className="place-header">
        <span className="place-icon">{CATEGORY_ICONS[place.category] || '📍'}</span>
        <div className="place-info">
          <h4 className="place-name">{place.name}</h4>
          <span className="place-category">{place.subcategory}</span>
        </div>
      </div>

      <div className="place-details">
        <div className="place-detail">
          <span className="detail-label">Cost:</span>
          <span className="detail-value">¥{place.cost_estimate.toLocaleString()}</span>
        </div>
        <div className="place-detail">
          <span className="detail-label">Duration:</span>
          <span className="detail-value">{place.duration_hours}h</span>
        </div>
        <div className="place-detail">
          <span className="detail-label">Rating:</span>
          <span className="detail-value">⭐ {place.rating.toFixed(1)}</span>
        </div>
      </div>

      {place.description && (
        <p className="place-description">{place.description}</p>
      )}

      <style>{`
        .place-card {
          background: var(--color-card);
          border-radius: var(--border-radius);
          padding: 1rem;
          box-shadow: var(--shadow-sm);
          transition: box-shadow 0.2s;
        }
        .place-card:hover {
          box-shadow: var(--shadow);
        }
        .place-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 0.75rem;
        }
        .place-icon {
          font-size: 1.5rem;
        }
        .place-info {
          flex: 1;
        }
        .place-name {
          font-size: 1rem;
          font-weight: 600;
          margin: 0;
        }
        .place-category {
          font-size: 0.875rem;
          color: var(--color-text-secondary);
        }
        .place-details {
          display: flex;
          gap: 1rem;
          flex-wrap: wrap;
          margin-bottom: 0.5rem;
        }
        .place-detail {
          display: flex;
          gap: 0.25rem;
          font-size: 0.875rem;
        }
        .detail-label {
          color: var(--color-text-secondary);
        }
        .detail-value {
          font-weight: 500;
        }
        .place-description {
          font-size: 0.875rem;
          color: var(--color-text-secondary);
          margin: 0;
          margin-top: 0.5rem;
        }
      `}</style>
    </div>
  )
}
