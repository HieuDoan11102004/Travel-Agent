import { useState } from 'react'
import { Preferences } from '../api'

interface PreferenceFormProps {
  onSubmit: (preferences: Preferences) => void
  loading?: boolean
}

const STYLE_OPTIONS = [
  { value: '', label: 'Any' },
  { value: 'cultural', label: 'Cultural' },
  { value: 'foodie', label: 'Foodie' },
  { value: 'nature', label: 'Nature' },
  { value: 'shopping', label: 'Shopping' },
  { value: 'nightlife', label: 'Nightlife' },
]

const MOBILITY_OPTIONS = [
  { value: '', label: 'Any' },
  { value: 'walking', label: 'Walking' },
  { value: 'public_transport', label: 'Public Transport' },
  { value: 'taxi', label: 'Taxi' },
]

export default function PreferenceForm({ onSubmit, loading }: PreferenceFormProps) {
  const [formData, setFormData] = useState({
    destination: 'Tokyo',
    days: '3',
    people: '2',
    budget: '100000',
    style: '',
    mobility: '',
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      destination: formData.destination,
      days: parseInt(formData.days),
      people: parseInt(formData.people),
      budget: parseInt(formData.budget),
      style: formData.style || undefined,
      mobility: formData.mobility || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="preference-form">
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Destination</label>
          <input
            type="text"
            name="destination"
            value={formData.destination}
            onChange={handleChange}
            className="form-input"
            placeholder="Tokyo"
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Days</label>
          <input
            type="number"
            name="days"
            value={formData.days}
            onChange={handleChange}
            className="form-input"
            min="1"
            max="30"
            required
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">People</label>
          <input
            type="number"
            name="people"
            value={formData.people}
            onChange={handleChange}
            className="form-input"
            min="1"
            max="20"
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">Budget (JPY)</label>
          <input
            type="number"
            name="budget"
            value={formData.budget}
            onChange={handleChange}
            className="form-input"
            min="1000"
            step="1000"
            required
          />
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Travel Style</label>
          <select
            name="style"
            value={formData.style}
            onChange={handleChange}
            className="form-input"
          >
            {STYLE_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Mobility</label>
          <select
            name="mobility"
            value={formData.mobility}
            onChange={handleChange}
            className="form-input"
          >
            {MOBILITY_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      <button
        type="submit"
        className="btn btn-primary"
        disabled={loading}
        style={{ width: '100%', marginTop: '1rem' }}
      >
        {loading ? 'Generating...' : 'Generate Itinerary'}
      </button>

      <style>{`
        .preference-form {
          max-width: 500px;
          margin: 0 auto;
        }
        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }
        @media (max-width: 500px) {
          .form-row {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </form>
  )
}
