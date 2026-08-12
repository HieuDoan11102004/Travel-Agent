"""Tests for the travel planner agent."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.agent.nodes import (
    _parse_preferences_fallback,
    _build_search_query,
    _fallback_select_places,
)
from app.models.preferences import UserPreferences


# Sample search results
SAMPLE_RESULTS = [
    {
        "place": {
            "id": "p1",
            "name": "Senso-ji Temple",
            "category": "attraction",
            "subcategory": "temple",
            "location": {"lat": 35.7, "lng": 139.7},
            "cost_estimate": 0,
            "duration_hours": 2.0,
            "popularity": "high",
            "rating": 4.7,
        },
        "score": 1.0,
    },
    {
        "place": {
            "id": "p2",
            "name": "Tokyo Skytree",
            "category": "attraction",
            "subcategory": "tower",
            "location": {"lat": 35.71, "lng": 139.81},
            "cost_estimate": 3100,
            "duration_hours": 2.5,
            "popularity": "high",
            "rating": 4.5,
        },
        "score": 0.9,
    },
    {
        "place": {
            "id": "p3",
            "name": "Sushi Restaurant",
            "category": "restaurant",
            "subcategory": "sushi",
            "location": {"lat": 35.67, "lng": 139.76},
            "cost_estimate": 5000,
            "duration_hours": 1.5,
            "popularity": "medium",
            "rating": 4.3,
        },
        "score": 0.8,
    },
]


class TestParsePreferencesFallback:
    """Tests for rule-based preference parsing fallback."""

    def test_parse_basic(self):
        prefs = _parse_preferences_fallback("Tokyo 3 days, 2 people")
        assert prefs.destination == "Tokyo"
        assert prefs.days == 3
        assert prefs.people == 2

    def test_parse_budget(self):
        prefs = _parse_preferences_fallback("Tokyo 3 days 500,000 yen")
        assert prefs.budget == 500000

    def test_parse_style(self):
        prefs = _parse_preferences_fallback("Tokyo cultural trip 3 days")
        assert prefs.style == "cultural"

    def test_parse_osaka(self):
        prefs = _parse_preferences_fallback("Osaka 2 days")
        assert prefs.destination == "Osaka"


class TestBuildSearchQuery:
    def test_basic_query(self):
        prefs = UserPreferences(
            destination="Tokyo", days=3, people=2, budget=100000
        )
        query = _build_search_query(prefs)
        assert "Tokyo" in query

    def test_query_with_style(self):
        prefs = UserPreferences(
            destination="Tokyo",
            days=3,
            people=2,
            budget=100000,
            style="foodie",
        )
        query = _build_search_query(prefs)
        assert "Tokyo" in query
        assert "foodie" in query

    def test_query_with_implicit_prefs(self):
        prefs = UserPreferences(
            destination="Tokyo",
            days=3,
            people=2,
            budget=100000,
            implicit_preferences="quiet temples and local food",
        )
        query = _build_search_query(prefs)
        assert "quiet temples" in query


class TestFallbackSelectPlaces:
    def test_select_places(self):
        prefs = UserPreferences(
            destination="Tokyo", days=3, people=2, budget=100000
        )
        selected = _fallback_select_places(SAMPLE_RESULTS, prefs)
        assert len(selected) >= 1
        assert len(selected) <= 5

    def test_respects_time_limit(self):
        prefs = UserPreferences(
            destination="Tokyo", days=3, people=2, budget=100000
        )
        long_results = SAMPLE_RESULTS * 3
        selected = _fallback_select_places(long_results, prefs)
        total_hours = sum(p["duration_hours"] for p in selected)
        assert total_hours <= 9.5  # Allow small buffer


class TestTravelPlannerAgent:
    """Tests for the full agent with mocked LLM."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM client that returns predictable responses."""
        mock = MagicMock()
        mock.extract_preferences = AsyncMock(
            return_value={
                "destination": "Tokyo",
                "days": 2,
                "people": 2,
                "budget": 100000,
                "categories": [],
                "style": None,
                "mobility": None,
                "implicit_preferences": None,
                "planning_notes": None,
            }
        )
        mock.plan_day = AsyncMock(
            return_value={
                "selected_places": [1, 2],
                "start_time": "09:00",
                "theme": "Temple & Dining",
                "notes": "Great combination",
            }
        )
        mock.critique_day = AsyncMock(
            return_value={
                "passed": True,
                "issues": [],
                "suggestions": [],
                "reasoning": "Looks good",
            }
        )
        mock.should_continue = AsyncMock(
            return_value={
                "ready": True,
                "concerns": [],
                "suggestions": [],
            }
        )
        return mock

    @pytest.fixture
    def mock_agent(self, mock_llm):
        """Create agent with mocked dependencies."""
        from app.retrieval.embedder import Embedder
        from app.retrieval.hybrid import HybridSearcher
        from app.retrieval.reranker import Reranker
        from app.constraints.validator import ConstraintValidator

        embedder = MagicMock(spec=Embedder)
        searcher = MagicMock(spec=HybridSearcher)
        reranker = MagicMock(spec=Reranker)
        validator = MagicMock(spec=ConstraintValidator)

        searcher.search.return_value = SAMPLE_RESULTS
        reranker.rerank.return_value = SAMPLE_RESULTS
        validator.validate_day_plan.return_value = (True, [])

        with patch("app.agent.nodes.get_llm_client", return_value=mock_llm):
            from app.agent.graph import TravelPlannerAgent

            agent = TravelPlannerAgent(embedder, searcher, reranker, validator)
            yield agent

    def test_agent_initialization(self, mock_agent):
        assert mock_agent.graph is not None

    def test_agent_run_with_mock(self, mock_agent):
        """Test agent run with mocked LLM."""
        result = mock_agent.run("Tokyo 2 days, 2 people")
        assert "preferences" in result
        assert result["preferences"] is not None

    def test_agent_extracts_prefs(self, mock_agent, mock_llm):
        """Test that LLM is called for preference extraction."""
        mock_agent.run("Tokyo 2 days")
        mock_llm.extract_preferences.assert_called_once()

    def test_agent_plans_days(self, mock_agent, mock_llm):
        """Test that LLM is called for day planning."""
        mock_agent.run("Tokyo 2 days")
        assert mock_llm.plan_day.call_count == 2  # 2 days

    def test_agent_critiques_days(self, mock_agent, mock_llm):
        """Test that LLM is called for critique."""
        mock_agent.run("Tokyo 2 days")
        assert mock_llm.critique_day.call_count == 2  # 2 days
