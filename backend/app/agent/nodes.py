"""LangGraph agent nodes for travel planning."""

import json
from datetime import datetime, timedelta
from typing import Literal

from app.agent.state import AgentState
from app.models.preferences import UserPreferences
from app.models.place import Place
from app.models.day_plan import DayPlan
from app.models.itinerary import Itinerary
from app.retrieval.embedder import Embedder
from app.retrieval.hybrid import HybridSearcher
from app.retrieval.reranker import Reranker
from app.constraints.validator import ConstraintValidator


MAX_ITERATIONS = 3


def create_agent_nodes(
    embedder: Embedder,
    searcher: HybridSearcher,
    reranker: Reranker,
    validator: ConstraintValidator,
):
    """Create agent nodes with dependencies injected."""

    def extract_prefs(state: AgentState) -> AgentState:
        """Extract user preferences from natural language input."""
        user_input = state.get("user_input", "")

        # Simple rule-based extraction (in production, use LLM)
        preferences = _parse_preferences(user_input)

        return {
            **state,
            "preferences": preferences,
            "iteration": 0,
        }

    def retrieve_places(state: AgentState) -> AgentState:
        """Retrieve relevant places using hybrid search."""
        preferences = state.get("preferences")
        if not preferences:
            return {**state, "error": "No preferences extracted"}

        # Build search query from preferences
        query = _build_search_query(preferences)

        # Search with category filters
        categories = preferences.categories if preferences.categories else None
        results = searcher.search(query, top_k=50, categories=categories)

        # Rerank based on preferences
        reranked = reranker.rerank(results, preferences=preferences)

        return {
            **state,
            "retrieved_places": reranked,
        }

    def plan_day(state: AgentState) -> AgentState:
        """Generate day plan for current day."""
        preferences = state.get("preferences")
        places = state.get("retrieved_places", [])
        current_day = state.get("current_day", 0)
        day_plans = state.get("day_plans", [])

        if not preferences or not places:
            return {**state, "error": "Missing preferences or places"}

        # Calculate date for this day
        start_date = datetime.now()
        day_date = (start_date + timedelta(days=current_day)).strftime("%Y-%m-%d")

        # Select places for this day
        day_places = _select_places_for_day(
            places,
            preferences,
            current_day,
            len(day_plans),
        )

        # Create day plan
        day_plan = DayPlan(
            date=day_date,
            places=[Place(**p["place"]) for p in day_places],
        )
        day_plan.calculate_totals()
        day_plan.travel_time_minutes = _estimate_travel_time(day_plan.places)

        updated_day_plans = day_plans + [day_plan]

        return {
            **state,
            "current_day": current_day + 1,
            "day_plans": updated_day_plans,
        }

    def critic(state: AgentState) -> AgentState:
        """Validate current day plan against constraints."""
        preferences = state.get("preferences")
        day_plans = state.get("day_plans", [])
        iteration = state.get("iteration", 0)

        if not preferences or not day_plans:
            return {**state, "violations": [], "iteration": iteration}

        # Validate the most recent day plan
        latest_day = day_plans[-1]
        passed, violations = validator.validate_day_plan(latest_day, preferences)

        if violations and iteration < MAX_ITERATIONS:
            # Try to fix by adjusting places
            return {
                **state,
                "violations": violations,
                "iteration": iteration + 1,
            }

        return {
            **state,
            "violations": violations if violations else [],
            "iteration": iteration,
        }

    def finalize(state: AgentState) -> AgentState:
        """Finalize the itinerary."""
        preferences = state.get("preferences")
        day_plans = state.get("day_plans", [])
        violations = state.get("violations", [])

        if not preferences:
            return {**state, "error": "No preferences available"}

        # Calculate totals
        total_cost = sum(day.total_cost for day in day_plans)
        total_hours = sum(day.total_hours for day in day_plans)

        # Create final itinerary
        itinerary = Itinerary(
            days=day_plans,
            total_cost=total_cost,
            total_hours=total_hours,
            constraints_satisfied=len(violations) == 0,
            violations=violations,
            preferences_summary=f"{preferences.days} days in {preferences.destination} for {preferences.people} people",
        )

        return {
            **state,
            "itinerary_result": itinerary.model_dump(),
        }

    def should_continue_loop(state: AgentState) -> Literal["plan_day", "finalize"]:
        """Decide whether to continue planning days or finalize."""
        preferences = state.get("preferences")
        current_day = state.get("current_day", 0)

        if preferences and current_day < preferences.days:
            return "plan_day"
        return "finalize"

    return {
        "extract_prefs": extract_prefs,
        "retrieve_places": retrieve_places,
        "plan_day": plan_day,
        "critic": critic,
        "finalize": finalize,
        "should_continue_loop": should_continue_loop,
    }


def _parse_preferences(user_input: str) -> UserPreferences:
    """Parse user input into preferences (simple rule-based)."""
    text = user_input.lower()

    # Extract destination
    destination = "Tokyo"
    if "osaka" in text:
        destination = "Osaka"
    elif "kyoto" in text:
        destination = "Kyoto"

    # Extract days
    days = 3
    import re
    day_match = re.search(r"(\d+)\s*day", text)
    if day_match:
        days = int(day_match.group(1))

    # Extract people
    people = 2
    people_match = re.search(r"(\d+)\s*(?:people|person|traveler)", text)
    if people_match:
        people = int(people_match.group(1))

    # Extract budget
    budget = 100000
    budget_match = re.search(r"([\d,]+)\s*(?:yen|jpy)", text)
    if budget_match:
        budget = int(budget_match.group(1).replace(",", ""))

    # Extract style
    style = None
    if "cultural" in text or "culture" in text:
        style = "cultural"
    elif "foodie" in text or "food" in text:
        style = "foodie"
    elif "shopping" in text:
        style = "shopping"

    return UserPreferences(
        destination=destination,
        days=days,
        people=people,
        budget=budget,
        style=style,
    )


def _build_search_query(preferences: UserPreferences) -> str:
    """Build search query from preferences."""
    parts = [preferences.destination]

    if preferences.style:
        parts.append(preferences.style)

    if preferences.categories:
        parts.extend(preferences.categories)

    return " ".join(parts)


def _select_places_for_day(
    all_places: list[dict],
    preferences: UserPreferences,
    current_day: int,
    total_days: int,
) -> list[dict]:
    """Select places for a single day."""
    # Simple selection: take top places that fit in a day
    selected = []
    total_hours = 0
    max_hours = 9.0

    for place_result in all_places:
        place = place_result["place"]
        duration = place.get("duration_hours", 1.0)

        if total_hours + duration <= max_hours:
            # Check category balance
            cat = place.get("category", "")
            cat_count = sum(1 for p in selected if p["place"].get("category") == cat)

            # Prefer variety
            if cat_count < 3 or cat in ["restaurant"]:
                selected.append(place_result)
                total_hours += duration

        if total_hours >= max_hours or len(selected) >= 5:
            break

    return selected


def _estimate_travel_time(places: list[Place]) -> int:
    """Estimate total travel time between places in minutes."""
    if len(places) < 2:
        return 0

    # Simple estimate: average 15 min between places
    return (len(places) - 1) * 15
