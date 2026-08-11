# Travel Planner Agent — Design

**Date**: 2026-08-11
**Status**: Approved

## 1. Overview

**Name**: Travel Planner Agent
**Type**: AI Agent for travel itinerary generation
**Core functionality**: Given user preferences, generate day-by-day itinerary with places, budget, timing
**Target users**: Travelers to Japan (starting with Tokyo)

## 2. Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12.3 |
| LLM | GPT-4o-mini (OpenAI) |
| Agent Framework | LangGraph 0.2.x + LangChain 0.3.x |
| API | FastAPI |
| Frontend | React |
| Vector DB | Qdrant 0.22+ |
| Relational DB | PostgreSQL 16+ |
| Local Analytics | DuckDB + SQLite |
| Search | BM25 + Hybrid (RRF) |
| Package Manager | uv |
| Live Search | Tavily / SerpAPI |
| Deployment | Docker + Railway/Render |

## 3. Architecture

```
┌─────────────┐      REST API       ┌─────────────────┐
│   React     │ ──────────────────► │    FastAPI      │
│   Frontend  │ ◄────────────────── │    Backend      │
└─────────────┘                     └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        ▼                        │
                    │  ┌─────────────────────────────────────────┐   │
                    │  │           LangGraph Agent                │   │
                    │  │  ┌─────────┐ ┌─────────┐ ┌───────────┐ │   │
                    │  │  │Extract  │→│Retrieve │→│  Planner  │ │   │
                    │  │  │Prefs    │ │  (RAG)  │ │  Generate │ │   │
                    │  │  └─────────┘ └─────────┘ └─────┬─────┘ │   │
                    │  │                               ▼       │   │
                    │  │                        ┌───────────┐  │   │
                    │  │                        │  Critic   │  │   │
                    │  │                        │(validate) │  │   │
                    │  │                        └─────┬─────┘  │   │
                    │  │                              │◄──────┘   │
                    │  │                              │(loop≤3)   │
                    │  │                        ┌─────▼─────┐    │   │
                    │  │                        │  Final    │    │   │
                    │  │                        │Itinerary  │    │   │
                    │  └────────────────────────┴───────────┴────┘   │
                    │                                           │
                    │  ┌──────────────┐  ┌────────────────────┐   │
                    │  │  DuckDB/     │  │  Qdrant (vectors)   │   │
                    │  │  SQLite      │  │  + BM25 fallback    │   │
                    │  │  (places)    │  │                     │   │
                    │  └──────────────┘  └────────────────────┘   │
                    │                                           │
                    │  ┌──────────────┐  ┌────────────────────┐   │
                    │  │ PostgreSQL   │  │ Tavily/SerpAPI     │   │
                    │  │ (sessions,   │  │ (live search)      │   │
                    │  │  history)    │  │                    │   │
                    │  └──────────────┘  └────────────────────┘   │
                    └───────────────────────────────────────────┘   │
                                                                     │
                    ┌───────────────────────────────────────────┐   │
                    │            External Services               │   │
                    │  OpenAI GPT-4o-mini (LLM)                  │   │
                    │  OpenAI Embeddings (vectorization)          │   │
                    └───────────────────────────────────────────┘   │
```

## 4. Data Models

### Place
```python
class Place(BaseModel):
    id: str                    # unique
    name: str
    category: Literal["attraction", "restaurant", "hotel", "transport", "shopping"]
    subcategory: str
    location: {"lat": float, "lng": float}
    cost_estimate: int        # JPY
    duration_hours: float
    opening_hours: dict | None
    popularity: Literal["high", "medium", "low"]
    rating: float              # 0-5
```

### DayPlan
```python
class DayPlan(BaseModel):
    date: str                  # YYYY-MM-DD
    places: List[Place]
    total_cost: int
    total_hours: float
    travel_time_minutes: int
```

### Itinerary
```python
class Itinerary(BaseModel):
    days: List[DayPlan]
    total_cost: int
    constraints_satisfied: bool
    violations: List[str]
```

### UserPreferences (extracted)
```python
class UserPreferences(BaseModel):
    destination: str
    days: int
    people: int
    budget: int                # JPY
    categories: List[str] | None
    style: str | None          # e.g., "cultural", "foodie"
    mobility: str | None       # e.g., "walking", "public_transport"
```

## 5. Agent Flow (LangGraph)

### State Machine
```
Input → ExtractPrefs → RetrievePlaces → GenerateDayPlan → Critic
                                                            │
                                           violations > 0 ─┤
                                           (max 3 loops)   │
                                                            ▼
                                                       FinalOutput
```

### State Shape
```python
class AgentState(TypedDict):
    user_input: str
    preferences: UserPreferences | None
    retrieved_places: List[Place]
    current_day: int
    day_plans: List[DayPlan]
    violations: List[str]
    iteration: int
```

### Nodes
1. **extract_prefs** — Parse natural language → UserPreferences
2. **retrieve_places** — RAG pipeline (hybrid search)
3. **plan_day** — Generate DayPlan for current day
4. **critic** — Validate constraints, return violations
5. **finalize** — Combine day plans, compute totals

## 6. Constraints

### Hard Constraints (must satisfy or list violations)
| Constraint | Rule |
|------------|------|
| Daily cost | ≤ budget_total / days × 1.1 |
| Daily hours | ≤ 10 hours |
| Daily travel time | ≤ 90 minutes |
| Place availability | All places open on visit date |

### Soft Constraints (optimize)
| Constraint | Goal |
|------------|------|
| Category balance | Mix of attractions, food, transport |
| Travel time | Minimize total travel |
| Popularity | Distribute across high/medium/low |

## 7. Retrieval Pipeline

1. **Query preprocessing** — Extract keywords + embed query
2. **Parallel retrieval**:
   - BM25 keyword search → top 50
   - Qdrant vector similarity → top 50
3. **Fusion** — Reciprocal Rank Fusion (RRF)
4. **Rerank** — Score by preference compatibility
5. **Filter** — Remove closed places, enforce category balance

## 8. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/itinerary` | Generate itinerary from preferences |
| `GET` | `/api/v1/itinerary/{id}` | Get existing itinerary |
| `GET` | `/api/v1/itinerary/{id}/places` | Get places in itinerary |
| `POST` | `/api/v1/places/search` | Search places (hybrid) |
| `GET` | `/api/v1/health` | Health check |

### Request: POST /api/v1/itinerary
```json
{
  "destination": "Tokyo",
  "days": 3,
  "people": 2,
  "budget": 500000,
  "preferences": {
    "categories": ["attraction", "restaurant"],
    "style": "cultural",
    "mobility": "walking"
  }
}
```

## 9. Frontend (React)

### Pages
| Route | Description |
|-------|-------------|
| `/` | Home: input form (destination, days, budget, preferences) |
| `/itinerary/:id` | Display itinerary with day-by-day breakdown |
| `/history` | Past itineraries |

### Components
- `PreferenceForm` — Input form with validation
- `ItineraryView` — Day cards with places, costs, travel time
- `PlaceCard` — Individual place details
- `ConstraintStatus` — Shows satisfied/violated constraints

## 10. Project Structure

```
travel-planner/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py     # v1 router
│   │   │       ├── itinerary.py  # Itinerary endpoints
│   │   │       └── places.py     # Place search endpoints
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py          # LangGraph definition
│   │   │   ├── nodes.py          # Extract, Retrieve, Plan, Critic, Finalize
│   │   │   └── state.py          # AgentState
│   │   ├── retrieval/
│   │   │   ├── __init__.py
│   │   │   ├── hybrid.py         # BM25 + vector fusion
│   │   │   ├── reranker.py
│   │   │   └── embedder.py       # OpenAI embeddings
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── place.py
│   │   │   ├── day_plan.py
│   │   │   ├── itinerary.py
│   │   │   └── preferences.py
│   │   ├── constraints/
│   │   │   ├── __init__.py
│   │   │   ├── validator.py      # Hard/soft constraint checks
│   │   │   └── types.py
│   │   └── data/
│   │       ├── __init__.py
│   │       ├── duckdb_client.py
│   │       ├── qdrant_client.py
│   │       └── postgres_client.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_constraints.py
│   │   └── test_agent.py
│   ├── seed_data/
│   │   └── tokyo_places.json
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .python-version
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── api/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## 11. Testing Strategy

| Level | Scope | Tools |
|-------|-------|-------|
| **Unit** | Models, constraints | `pytest` |
| **Integration** | RAG pipeline, DB | `pytest` + test DBs |
| **E2E** | Full flow | `pytest` + `httpx` |

### Acceptance Criteria
- [ ] User can input: "Tokyo 3 days, 2 people, 500000 yen"
- [ ] Returns valid itinerary with 3 DayPlans
- [ ] All constraints satisfied (or violations listed)
- [ ] Response time < 30 seconds
- [ ] Unit tests pass for models and constraints

## 12. Environment Variables

```env
# OpenAI
OPENAI_API_KEY=

# Database
POSTGRES_URL=postgresql://user:pass@localhost:5432/travel
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Search (optional)
TAVILY_API_KEY=
SERPAPI_API_KEY=

# App
LOG_LEVEL=INFO
ENV=development
```
