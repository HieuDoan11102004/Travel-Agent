# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered travel itinerary generator for Japan using LangGraph agent with hybrid search (BM25 + vector RRF) and constraint validation.

## Commands

### Backend (Python)
```bash
cd backend
uv sync                    # Install dependencies
uv run pytest               # Run all tests
uv run pytest tests/test_x.py::TestY -v  # Run specific test
uv run uvicorn app.main:app --reload  # Run dev server
uv run python scripts/seed_data.py      # Seed places data
```

### Frontend (React)
```bash
cd frontend
npm install                 # Install dependencies
npm run dev                 # Run dev server (port 5173)
npm run build               # Production build
```

### Docker
```bash
docker-compose up           # Start all services
docker-compose up --build   # Rebuild and start
docker-compose down         # Stop services
```

### Linting
```bash
cd backend && uv run ruff check .
cd backend && uv run mypy app/
```

## Architecture

### Backend: LangGraph Agent Pipeline
```
Input → extract_prefs → retrieve_places → plan_day → critic → (loop ≤3) → finalize
```

- **agent/graph.py**: `TravelPlannerAgent` - builds and compiles the StateGraph
- **agent/nodes.py**: Node functions (extract_prefs, retrieve_places, plan_day, critic, finalize)
- **agent/state.py**: `AgentState` TypedDict defining the workflow state
- **constraints/**: Hard constraints (daily cost, hours, travel time) validated by critic

### Retrieval Pipeline
```
Query → BM25 search → Vector search → RRF fusion → Reranker → Results
```

- **retrieval/embedder.py**: OpenAI embeddings
- **retrieval/bm25.py**: Keyword search with rank-bm25
- **retrieval/hybrid.py**: Reciprocal Rank Fusion combining BM25 + vector
- **retrieval/reranker.py**: Preference-aware reranking with category balancing

### API Structure
- **app/api/v1/router.py**: Mounts all v1 endpoints
- **app/main.py**: FastAPI app with CORS and lifespan
- **app/config.py**: Settings via pydantic-settings from .env

### Data Models
All Pydantic models in **app/models/**: Place, DayPlan, Itinerary, UserPreferences

### Storage
- **DuckDB**: Local places data (seeded from JSON)
- **Qdrant**: Vector embeddings for semantic search
- **PostgreSQL**: Itinerary storage and search history

## Key Patterns

### Agent Node Functions
Node functions receive `AgentState` dict, return updated dict. Use `_select_places_for_day()` helper to choose places respecting daily time limits (~9h).

### Constraint Validation
**constraints/types.py** defines `Constraint` objects with `check_func`. Validator runs all hard constraints and collects violations.

### RRF Fusion
Hybrid search uses Reciprocal Rank Fusion with k=60: `score = Σ(1 / (k + rank))` across search methods.
