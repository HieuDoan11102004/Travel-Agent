import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import ItineraryView from './pages/ItineraryView'
import History from './pages/History'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/itinerary/:id" element={<ItineraryView />} />
      <Route path="/history" element={<History />} />
    </Routes>
  )
}

export default App
