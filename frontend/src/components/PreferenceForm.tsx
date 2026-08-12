import { useState } from 'react'
import { Preferences } from '../api'

interface PreferenceFormProps {
  onSubmit: (preferences: Preferences, userInput?: string) => void
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

const PLACEHOLDER_TEXT = `Tell us about your dream trip to Japan...

Example: "Plan a romantic 5-day trip to Kyoto for my wife and me. We love exploring hidden temples, enjoying local cuisine at izakayas, and walking through bamboo groves. We're not fans of crowded tourist spots. Budget around 200,000 yen total."`

type InputMode = 'form' | 'text'

export default function PreferenceForm({ onSubmit, loading }: PreferenceFormProps) {
  const [mode, setMode] = useState<InputMode>('form')
  const [formData, setFormData] = useState({
    destination: 'Tokyo',
    days: '3',
    people: '2',
    budget: '100000',
    style: '',
    mobility: '',
  })
  const [freeTextInput, setFreeTextInput] = useState('')

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleFormSubmit = (e: React.FormEvent) => {
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

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!freeTextInput.trim()) return
    // Extract basic info for the API call, rest from LLM
    onSubmit(
      {
        destination: 'Japan', // LLM will extract actual destination
        days: 3,
        people: 2,
        budget: 100000,
      },
      freeTextInput
    )
  }

  return (
    <div className="preference-form">
      {/* Mode Toggle */}
      <div className="mode-toggle">
        <button
          type="button"
          className={`toggle-btn ${mode === 'form' ? 'active' : ''}`}
          onClick={() => setMode('form')}
        >
          Quick Form
        </button>
        <button
          type="button"
          className={`toggle-btn ${mode === 'text' ? 'active' : ''}`}
          onClick={() => setMode('text')}
        >
          Describe Your Trip
        </button>
      </div>

      {/* Quick Form Mode */}
      {mode === 'form' && (
        <form onSubmit={handleFormSubmit} className="form-content">
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
        </form>
      )}

      {/* Free Text Mode */}
      {mode === 'text' && (
        <form onSubmit={handleTextSubmit} className="form-content">
          <div className="form-group" style={{ width: '100%' }}>
            <label className="form-label">Describe Your Trip</label>
            <textarea
              value={freeTextInput}
              onChange={(e) => setFreeTextInput(e.target.value)}
              className="form-input free-text-input"
              placeholder={PLACEHOLDER_TEXT}
              rows={8}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !freeTextInput.trim()}
            style={{ width: '100%', marginTop: '1rem' }}
          >
            {loading ? 'Generating...' : 'Generate Itinerary'}
          </button>
        </form>
      )}

      <style>{`
        .preference-form {
          max-width: 500px;
          margin: 0 auto;
        }
        .mode-toggle {
          display: flex;
          justify-content: center;
          gap: 0;
          margin-bottom: 1.5rem;
          background: var(--color-bg-secondary, #f3f4f6);
          border-radius: 8px;
          padding: 4px;
        }
        .toggle-btn {
          flex: 1;
          padding: 0.75rem 1rem;
          border: none;
          background: transparent;
          color: var(--color-text-secondary, #6b7280);
          font-weight: 500;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .toggle-btn:hover {
          color: var(--color-text, #1f2937);
        }
        .toggle-btn.active {
          background: white;
          color: var(--color-primary, #2563eb);
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .form-content {
          animation: fadeIn 0.2s ease;
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-5px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }
        .free-text-input {
          min-height: 200px;
          resize: vertical;
          line-height: 1.6;
        }
        @media (max-width: 500px) {
          .form-row {
            grid-template-columns: 1fr;
          }
          .toggle-btn {
            padding: 0.6rem 0.5rem;
            font-size: 0.875rem;
          }
        }
      `}</style>
    </div>
  )
}
