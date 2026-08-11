import PlaceCard from './PlaceCard'
import ConstraintStatus from './ConstraintStatus'
import { Place } from '../api'

interface DayPlan {
  date: string
  places: Place[]
  total_cost: number
  total_hours: number
  travel_time_minutes: number
}

interface ItineraryViewProps {
  days: DayPlan[]
  totalCost: number
  totalHours: number
  constraintsSatisfied: boolean
  violations: string[]
}

export default function ItineraryView({
  days,
  totalCost,
  totalHours,
  constraintsSatisfied,
  violations,
}: ItineraryViewProps) {
  return (
    <div className="itinerary-view">
      <div className="itinerary-summary">
        <div className="summary-stat">
          <span className="stat-value">{days.length}</span>
          <span className="stat-label">Days</span>
        </div>
        <div className="summary-stat">
          <span className="stat-value">¥{totalCost.toLocaleString()}</span>
          <span className="stat-label">Total Cost</span>
        </div>
        <div className="summary-stat">
          <span className="stat-value">{totalHours.toFixed(1)}h</span>
          <span className="stat-label">Total Hours</span>
        </div>
      </div>

      <ConstraintStatus satisfied={constraintsSatisfied} violations={violations} />

      <div className="day-plans">
        {days.map((day, index) => (
          <div key={index} className="day-plan">
            <div className="day-header">
              <h3>Day {index + 1}</h3>
              <span className="day-date">{day.date}</span>
            </div>

            <div className="day-meta">
              <span>💰 ¥{day.total_cost.toLocaleString()}</span>
              <span>⏱️ {day.total_hours.toFixed(1)}h</span>
              <span>🚶 {day.travel_time_minutes}min travel</span>
            </div>

            <div className="places-list">
              {day.places.map((place) => (
                <PlaceCard key={place.id} place={place} />
              ))}
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .itinerary-view {
          max-width: 800px;
          margin: 0 auto;
        }
        .itinerary-summary {
          display: flex;
          justify-content: space-around;
          background: var(--color-card);
          border-radius: var(--border-radius);
          padding: 1.5rem;
          margin-bottom: 1.5rem;
          box-shadow: var(--shadow);
        }
        .summary-stat {
          text-align: center;
        }
        .stat-value {
          display: block;
          font-size: 1.5rem;
          font-weight: 700;
          color: var(--color-primary);
        }
        .stat-label {
          font-size: 0.875rem;
          color: var(--color-text-secondary);
        }
        .day-plan {
          background: var(--color-card);
          border-radius: var(--border-radius);
          padding: 1.5rem;
          margin-bottom: 1rem;
          box-shadow: var(--shadow);
        }
        .day-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
        }
        .day-header h3 {
          margin: 0;
          color: var(--color-primary);
        }
        .day-date {
          color: var(--color-text-secondary);
          font-size: 0.875rem;
        }
        .day-meta {
          display: flex;
          gap: 1rem;
          font-size: 0.875rem;
          color: var(--color-text-secondary);
          margin-bottom: 1rem;
          padding-bottom: 0.75rem;
          border-bottom: 1px solid #e2e8f0;
        }
        .places-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
      `}</style>
    </div>
  )
}
