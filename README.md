# Travel Planner Agent

AI-powered travel itinerary generator for Japan (starting with Tokyo).

## Overview

Given user preferences (destination, days, budget, style), generates a day-by-day itinerary with places, costs, and travel times.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12.3 |
| LLM | GPT-4o-mini (OpenAI) |
| Agent Framework | LangGraph 0.2.x + LangChain 0.3.x |
| API | FastAPI |
| Frontend | React + Vite |
| Vector DB | Qdrant 0.22+ |
| Relational DB | PostgreSQL 16+ |
| Search | BM25 + Hybrid (RRF) |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose

### Setup

1. Clone the repository
2. Copy environment variables:
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your API keys
   ```

3. Start with Docker:
   ```bash
   docker-compose up
   ```

4. Or run locally:

   **Backend:**
   ```bash
   cd backend
   uv sync
   uv run uvicorn app.main:app --reload
   ```

   **Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Project Structure

```
travel-planner/
├── backend/              # FastAPI + LangGraph agent
│   ├── app/
│   │   ├── agent/       # LangGraph nodes & graph
│   │   ├── retrieval/   # RAG pipeline
│   │   ├── models/      # Pydantic models
│   │   └── constraints/ # Constraint validation
│   ├── tests/
│   └── seed_data/
├── frontend/             # React app
│   └── src/
│       ├── components/
│       └── pages/
└── docker-compose.yml
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/itinerary` | Generate itinerary |
| `GET` | `/api/v1/itinerary/{id}` | Get itinerary |
| `POST` | `/api/v1/places/search` | Search places |
| `GET` | `/api/v1/health` | Health check |

### Example Request

```bash
curl -X POST http://localhost:8000/api/v1/itinerary \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Tokyo",
    "days": 3,
    "people": 2,
    "budget": 500000,
    "preferences": {
      "style": "cultural",
      "mobility": "walking"
    }
  }'
```

## Development

### Running Tests

```bash
cd backend
uv run pytest
```

### Adding Seed Data

Edit `backend/seed_data/tokyo_places.json` and run the seeding script.

## License

MIT
