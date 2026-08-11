"""Tests for the travel planner agent."""

import pytest
from unittest.mock import MagicMock, patch

from app.agent.graph import TravelPlannerAgent
from app.agent.nodes import (
    _parse_preferences,
    _build_search_query,
    _select_places_for_day,
)
from app.models.preferences import UserPreferences


# Sample search results
SAMPLE_RESULTS = [
    {"place": {
        "id": "p1", "name": "Senso-ji Temple", "category": "attraction",
        "subcategory": "temple", "location": {"lat": 35.7, "lng": 139.7},
        "cost_estimate": 0, "duration_hours": 2.0, "popularity": "high", "rating": 4.7
    }, "score": 1.0},
    {"place": {
        "id": "p2", "name": "Tokyo Skytree", "category": "attraction",
        "subcategory": "tower", "location": {"lat": 35.71, "lng": 139.81},
        "cost_estimate": 3100, "duration_hours": 2.5, "popularity": "high", "rating": 4.5
    }, "score": 0.9},
    {"place": {
        "id": "p3", "name": "Sushi Restaurant", "category": "restaurant",
        "subcategory": "sushi", "location": {"lat": 35.67, "lng": 139.76},
        "cost_estimate": 5000, "duration_hours": 1.5, "popularity": "medium", "rating": 4.3
    }, "score": 0.8},
]


class TestParsePreferences:
    def test_parse_basic(self):
        prefs = _parse_preferences("Tokyo 3 days, 2 people")
        assert prefs.destination == "Tokyo"
        assert prefs.days == 3
        assert prefs.people == 2

    def test_parse_budget(self):
        prefs = _parse_preferences("Tokyo 3 days 500,000 yen")
        assert prefs.budget == 500000

    def test_parse_style(self):
        prefs = _parse_preferences("Tokyo cultural trip 3 days")
        assert prefs.style == "cultural"

    def test_parse_osaka(self):
        prefs = _parse_preferences("Osaka 2 days")
        assert prefs.destination == "Osaka"


class TestBuildSearchQuery:
    def test_basic_query(self):
        prefs = UserPreferences(destination="Tokyo", days=3, people=2, budget=100000)
        query = _build_search_query(prefs)
        assert "Tokyo" in query

    def test_query_with_style(self):
        prefs = UserPreferences(
            destination="Tokyo", days=3, people=2, budget=100000, style="foodie"
        )
        query = _build_search_query(prefs)
        assert "Tokyo" in query
        assert "foodie" in query


class TestSelectPlacesForDay:
    def test_select_places(self):
        prefs = UserPreferences(destination="Tokyo", days=3, people=2, budget=100000)
        selected = _select_places_for_day(SAMPLE_RESULTS, prefs, 0, 0)
        assert len(selected) >= 1
        assert len(selected) <= 5

    def test_respects_time_limit(self):
        prefs = UserPreferences(destination="Tokyo", days=3, people=2, budget=100000)
        # All results total > 9 hours
        long_results = SAMPLE_RESULTS * 3
        selected = _select_places_for_day(long_results, prefs, 0, 0)
        total_hours = sum(p["place"]["duration_hours"] for p in selected)
        assert total_hours <= 9.5  # Allow small buffer


class TestTravelPlannerAgent:
    @pytest.fixture
    def mock_agent(self):
        """Create agent with mocked dependencies."""
        from app.retrieval.embedder import Embedder
        from app.retrieval.hybrid import HybridSearcher
        from app.retrieval.reranker import Reranker
        from app.constraints.validator import ConstraintValidator

        embedder = MagicMock(spec=Embedder)
        searcher = MagicMock(spec=HybridSearcher)
        reranker = MagicMock(spec=Reranker)
        validator = MagicMock(spec=ConstraintValidator)

        # Mock searcher to return sample results
        searcher.search.return_value = SAMPLE_RESULTS
        reranker.rerank.return_value = SAMPLE_RESULTS
        validator.validate_day_plan.return_value = (True, [])

        return TravelPlannerAgent(embedder, searcher, reranker, validator)

    def test_agent_initialization(self, mock_agent):
        assert mock_agent.graph is not None

    def test_agent_run(self, mock_agent):
        result = mock_agent.run("Tokyo 2 days, 2 people")
        assert "preferences" in result
        assert result["preferences"] is not None

    def test_agent_run_with_budget(self, mock_agent):
        result = mock_agent.run("Tokyo 3 days, 100,000 yen")
        assert result["preferences"].budget == 100000
