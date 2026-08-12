import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
})

export interface Preferences {
  destination: string
  days: number
  people: number
  budget: number
  style?: string
  mobility?: string
  categories?: string[]
}

export interface ItineraryRequest {
  destination: string
  days: number
  people: number
  budget: number
  preferences?: Partial<Preferences>
  user_input?: string
}

export interface ItineraryResponse {
  id: string
  status: string
  destination: string
  days: number
  itinerary?: any
  error?: string
}

export interface Place {
  id: string
  name: string
  category: string
  subcategory: string
  cost_estimate: number
  duration_hours: number
  rating: number
  description?: string
}

export const itineraryApi = {
  create: async (request: ItineraryRequest): Promise<ItineraryResponse> => {
    const response = await api.post('/itinerary', request)
    return response.data
  },

  get: async (id: string): Promise<ItineraryResponse> => {
    const response = await api.get(`/itinerary/${id}`)
    return response.data
  },

  getPlaces: async (id: string) => {
    const response = await api.get(`/itinerary/${id}/places`)
    return response.data
  },
}

export const placesApi = {
  search: async (query: string, limit = 20) => {
    const response = await api.post('/places/search', { query, limit })
    return response.data
  },

  getCategories: async () => {
    const response = await api.get('/places/categories')
    return response.data
  },
}

export default api
