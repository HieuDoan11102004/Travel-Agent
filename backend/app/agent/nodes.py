"""LangGraph agent nodes for travel planning with LLM."""

import logging
from datetime import datetime, timedelta
from typing import Literal

from app.agent.llm import get_llm_client
from app.agent.state import AgentState
from app.constraints.validator import ConstraintValidator
from app.models.day_plan import DayPlan
from app.models.itinerary import Itinerary
from app.models.place import Place
from app.models.preferences import UserPreferences
from app.retrieval.embedder import Embedder
from app.retrieval.hybrid import HybridSearcher
from app.retrieval.reranker import Reranker

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3
MAX_RETRY_ITERATIONS = 2


def create_agent_nodes(
    embedder: Embedder,
    searcher: HybridSearcher,
    reranker: Reranker,
    validator: ConstraintValidator,
):
    """Create agent nodes with dependencies injected."""

    async def extract_prefs(state: AgentState) -> AgentState:
        """Extract user preferences from natural language input using LLM."""
        user_input = state.get("user_input", "")

        llm = get_llm_client()
        try:
            extracted = await llm.extract_preferences(user_input)

            preferences = UserPreferences(
                destination=extracted.get("destination", "Tokyo"),
                days=extracted.get("days", 3),
                people=extracted.get("people", 1),
                budget=extracted.get("budget", 100000),
                categories=extracted.get("categories") or None,
                style=extracted.get("style"),
                mobility=extracted.get("mobility"),
                implicit_preferences=extracted.get("implicit_preferences"),
                planning_notes=extracted.get("planning_notes"),
            )

            logger.info(f"Extracted preferences: {preferences.summary()}")

            return {
                **state,
                "preferences": preferences,
                "iteration": 0,
                "llm_extracted": extracted,
            }
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}, falling back to rule-based")
            preferences = _parse_preferences_fallback(user_input)
            return {
                **state,
                "preferences": preferences,
                "iteration": 0,
                "llm_extracted": None,
            }

    def retrieve_places(state: AgentState) -> AgentState:
        """Retrieve relevant places using hybrid search."""
        preferences = state.get("preferences")
        if not preferences:
            return {**state, "error": "No preferences extracted"}

        query = _build_search_query(preferences)
        categories = preferences.categories if preferences.categories else None
        results = searcher.search(query, top_k=50, categories=categories)
        reranked = reranker.rerank(results, preferences=preferences)

        logger.info(f"Retrieved {len(reranked)} places for {preferences.destination}")

        return {
            **state,
            "retrieved_places": reranked,
        }

    async def plan_day(state: AgentState) -> AgentState:
        """Generate day plan for current day using LLM."""
        preferences = state.get("preferences")
        all_places = state.get("retrieved_places", [])
        current_day = state.get("current_day", 0)
        day_plans = state.get("day_plans", [])

        if not preferences or not all_places:
            return {**state, "error": "Missing preferences or places"}

        # Filter out already-visited places
        visited_ids = set()
        for dp in day_plans:
            for p in dp.places:
                visited_ids.add(p.id)

        available_places = [
            p for p in all_places
            if p["place"].get("id") not in visited_ids
        ]

        if not available_places:
            return {**state, "error": "No more places available"}

        start_date = datetime.now()
        day_date = (start_date + timedelta(days=current_day)).strftime("%Y-%m-%d")

        llm = get_llm_client()
        try:
            llm_plan = await llm.plan_day(
                day_number=current_day + 1,
                total_days=preferences.days,
                preferences=preferences,
                places=available_places,
            )

            selected_indices = llm_plan.get("selected_places", [])
            selected_places = []

            for idx in selected_indices:
                if 0 < idx <= len(available_places):
                    place_data = available_places[idx - 1]["place"]
                    selected_places.append(place_data)

            if not selected_places:
                selected_places = _fallback_select_places(available_places, preferences)

            theme = llm_plan.get("theme", "Explore")
            notes = llm_plan.get("notes", "")
            day_plan = DayPlan(
                date=day_date,
                places=[Place(**p) for p in selected_places],
                notes=f"Theme: {theme}\n{notes}",
            )
            day_plan.calculate_totals()
            day_plan.travel_time_minutes = _estimate_travel_time(day_plan.places)

            logger.info(f"Day {current_day + 1}: Planned {len(day_plan.places)} places")

            updated_day_plans = day_plans + [day_plan]

            return {
                **state,
                "current_day": current_day + 1,
                "day_plans": updated_day_plans,
                "current_llm_plan": llm_plan,
            }

        except Exception as e:
            logger.error(f"LLM day planning failed: {e}, using fallback")
            selected = _fallback_select_places(available_places, preferences)
            day_plan = DayPlan(
                date=day_date,
                places=[Place(**p) for p in selected],
            )
            day_plan.calculate_totals()
            day_plan.travel_time_minutes = _estimate_travel_time(day_plan.places)

            updated_day_plans = day_plans + [day_plan]

            return {
                **state,
                "current_day": current_day + 1,
                "day_plans": updated_day_plans,
            }

    async def critic(state: AgentState) -> AgentState:
        """Validate current day plan using LLM + hard constraints."""
        preferences = state.get("preferences")
        day_plans = state.get("day_plans", [])
        iteration = state.get("iteration", 0)

        if not preferences or not day_plans:
            return {**state, "violations": [], "iteration": iteration}

        latest_day = day_plans[-1]
        passed, hard_violations = validator.validate_day_plan(latest_day, preferences)

        hard_violation_msgs = [
            f"{v.constraint_name}: {v.message}" if hasattr(v, 'constraint_name') else str(v)
            for v in hard_violations
        ]

        llm = get_llm_client()
        try:
            llm_critique = await llm.critique_day(
                day_plan=latest_day.model_dump(),
                preferences=preferences,
                hard_violations=hard_violation_msgs,
            )

            llm_passed = llm_critique.get("passed", True)
            llm_issues = llm_critique.get("issues", [])

            all_violations = list(hard_violations)

            if not llm_passed:
                for issue in llm_issues:
                    all_violations.append(
                        type("SoftViolation", (), {
                            "constraint_name": "llm_suggestion",
                            "message": issue,
                            "severity": "soft",
                        })()
                    )

            should_retry = (
                (not passed or not llm_passed) and iteration < MAX_RETRY_ITERATIONS
            )
            next_iteration = iteration + 1 if should_retry else iteration

            logger.info(
                f"Critique day {len(day_plans)}: "
                f"hard_pass={passed}, llm_pass={llm_passed}"
            )

            return {
                **state,
                "violations": all_violations,
                "iteration": next_iteration,
                "llm_critique": llm_critique,
            }

        except Exception as e:
            logger.error(f"LLM critique failed: {e}, using hard constraints only")
            return {
                **state,
                "violations": hard_violations,
                "iteration": iteration,
            }

    async def should_continue_loop(
        state: AgentState,
    ) -> Literal["plan_day", "finalize"]:
        """Decide whether to continue planning days or finalize using LLM."""
        preferences = state.get("preferences")
        current_day = state.get("current_day", 0)
        day_plans = state.get("day_plans", [])

        if not preferences:
            return "finalize"

        if current_day < preferences.days:
            return "plan_day"

        llm = get_llm_client()
        try:
            llm_decision = await llm.should_continue(
                completed_days=[dp.model_dump() for dp in day_plans],
                preferences=preferences,
            )

            if llm_decision.get("ready", True):
                return "finalize"
            else:
                concerns = llm_decision.get("concerns", [])
                logger.warning(f"LLM concerns: {concerns}")
                return "finalize"

        except Exception as e:
            logger.error(f"LLM continue decision failed: {e}")
            return "finalize"

    def finalize(state: AgentState) -> AgentState:
        """Finalize the itinerary."""
        preferences = state.get("preferences")
        day_plans = state.get("day_plans", [])
        violations = state.get("violations", [])

        if not preferences:
            return {**state, "error": "No preferences available"}

        total_cost = sum(day.total_cost for day in day_plans)
        total_hours = sum(day.total_hours for day in day_plans)

        violation_msgs = [
            v.message if hasattr(v, "message") else str(v)
            for v in violations
        ]

        itinerary = Itinerary(
            days=day_plans,
            total_cost=total_cost,
            total_hours=total_hours,
            constraints_satisfied=len(violations) == 0,
            violations=violation_msgs,
            preferences_summary=preferences.summary(),
        )

        return {
            **state,
            "itinerary_result": itinerary.model_dump(),
        }

    return {
        "extract_prefs": extract_prefs,
        "retrieve_places": retrieve_places,
        "plan_day": plan_day,
        "critic": critic,
        "finalize": finalize,
        "should_continue_loop": should_continue_loop,
    }


def _parse_preferences_fallback(user_input: str) -> UserPreferences:
    """Fallback rule-based parsing if LLM fails."""
    import re

    text = user_input.lower()

    destination = "Tokyo"
    if "osaka" in text:
        destination = "Osaka"
    elif "kyoto" in text:
        destination = "Kyoto"

    days = 3
    day_match = re.search(r"(\d+)\s*day", text)
    if day_match:
        days = int(day_match.group(1))

    people = 2
    people_match = re.search(r"(\d+)\s*(?:people|person|traveler)", text)
    if people_match:
        people = int(people_match.group(1))

    budget = 100000
    budget_match = re.search(r"([\d,]+)\s*(?:yen|jpy)", text)
    if budget_match:
        budget = int(budget_match.group(1).replace(",", ""))

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

    if preferences.implicit_preferences:
        parts.append(preferences.implicit_preferences[:100])

    return " ".join(parts)


def _fallback_select_places(
    all_places: list[dict],
    preferences: UserPreferences,
    max_places: int = 5,
    max_hours: float = 9.0,
) -> list[dict]:
    """Fallback selection if LLM fails - simple greedy with variety."""
    selected = []
    total_hours = 0

    for place_result in all_places:
        place = place_result["place"]
        duration = place.get("duration_hours", 1.0)

        if total_hours + duration <= max_hours:
            cat = place.get("category", "")
            cat_count = sum(1 for p in selected if p.get("category") == cat)

            if cat_count < 3 or cat in ["restaurant"]:
                selected.append(place)
                total_hours += duration

        if total_hours >= max_hours or len(selected) >= max_places:
            break

    return selected


def _estimate_travel_time(places: list[Place]) -> int:
    """Estimate total travel time between places in minutes."""
    if len(places) < 2:
        return 0
    return (len(places) - 1) * 15
