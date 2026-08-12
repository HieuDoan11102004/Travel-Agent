"""LLM client wrapper for travel planning agent with Langfuse tracing."""

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# Shared Langfuse client - singleton
_langfuse_client = None


def get_langfuse_client():
    """Get or create shared Langfuse client."""
    global _langfuse_client
    if _langfuse_client is None:
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            try:
                from langfuse import Langfuse
                _langfuse_client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_base_url,
                )
                logger.info("Langfuse client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}")
                _langfuse_client = None
        else:
            logger.debug("Langfuse keys not configured")
    return _langfuse_client

EXTRACT_PREFS_PROMPT = """You are a travel planning assistant. Extract user preferences.

Return a JSON object with:
- destination: The city/region (default: "Tokyo")
- days: Number of days (default: 3)
- people: Number of travelers (default: 1)
- budget: Total budget in JPY (default: 100000)
- categories: List of place types (attraction, restaurant, hotel, shopping)
- style: Travel style (cultural, foodie, nature, shopping, nightlife)
- mobility: Preferred transport (walking, public_transport, taxi)
- implicit_preferences: What user cares about but didn't state explicitly.
  Include vibe, pace, crowd tolerance, interests, dietary needs.
- planning_notes: Specific wishes like "avoid tourist traps" or "start late"

Keep categories as empty list if not mentioned."""

PLAN_DAY_PROMPT = """You are an expert travel planner for Japan.

CONTEXT:
- Destination: {destination}
- Daily budget: {daily_budget:,} JPY
- Total budget: {total_budget:,} JPY
- People: {people}
- Style: {style}
- Categories: {categories}
- Implicit preferences: {implicit}
- Planning notes: {notes}

AVAILABLE PLACES (choose 3-6):
{places}

PLAN THE DAY:
1. Select places within daily budget
2. Create geographic/logical flow (minimize backtracking)
3. Match user style and implicit preferences
4. Vary activity types (avoid 3 restaurants in a row unless requested)
5. Consider hours (assume 9am-10pm)

Return JSON:
- selected_places: List of place indices (1-based) in visiting order
- start_time: Recommended start time (e.g., "09:00")
- theme: Brief description of the day's theme/narrative
- notes: Why these places work well together"""

CRITIQUE_DAY_PROMPT = """You are a travel critic reviewing a Japan trip day plan.

USER PROFILE:
- Destination: {destination}
- Style: {style}
- Implicit preferences: {implicit}
- Planning notes: {notes}
- Daily budget: {daily_budget:,} JPY

HARD VIOLATIONS (must address):
{violations}

CURRENT DAY PLAN:
{places}

Evaluate and return JSON:
- passed: boolean - true if good, false if needs changes
- issues: list of specific concerns (empty if passed)
- suggestions: concrete improvement suggestions
- reasoning: brief explanation"""

SHOULD_CONTINUE_PROMPT = """Review the completed trip plan for {destination}.

TRIP OVERVIEW:
- {days} days total
- Style: {style}
- Implicit preferences: {implicit}

COMPLETED DAYS:
{days_list}

Evaluate if the itinerary is satisfying:
- Good variety across days?
- Matches implicit preferences?
- Any obvious gaps?
- Appropriate pacing?

Return JSON:
- ready: boolean - true if complete and satisfying
- concerns: issues to address (empty if ready)
- suggestions: how to improve if not ready"""


class LLMClient:
    """Async LLM client for travel planning decisions with Langfuse tracing."""

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.3):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = model
        self.temperature = temperature

    def _get_langfuse(self):
        """Get shared Langfuse client."""
        return get_langfuse_client()

    async def extract_preferences(self, user_input: str) -> dict[str, Any]:
        """Extract structured preferences and implicit preferences from free-text."""
        langfuse = self._get_langfuse()

        if langfuse:
            with langfuse.start_as_current_observation(
                name="extract-preferences",
                input={"user_input": user_input},
                metadata={
                    "model": self.model,
                    "temperature": self.temperature,
                },
            ) as observation:
                response = await self._call_llm(
                    system_prompt=EXTRACT_PREFS_PROMPT,
                    user_message=user_input,
                )
                result = json.loads(response)
                observation.output = result
                return result
        else:
            return json.loads(
                await self._call_llm(
                    system_prompt=EXTRACT_PREFS_PROMPT,
                    user_message=user_input,
                )
            )

    async def plan_day(
        self,
        day_number: int,
        total_days: int,
        preferences,
        places: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Select and sequence places for a day using LLM judgment."""
        budget_per_day = preferences.daily_budget

        places_text = []
        for i, p in enumerate(places):
            place = p["place"]
            cost = place.get("cost_estimate", 0)
            duration = place.get("duration_hours", 1)
            rating = place.get("rating", "N/A")
            tags = ", ".join(place.get("tags", [])[:3])
            desc = place.get("description", "")[:150]
            cat = place.get("category", "unknown")
            places_text.append(
                f"{i+1}. {place['name']} ({cat})\n"
                f"   Cost: {cost} JPY, Duration: {duration}h\n"
                f"   Rating: {rating}, Tags: {tags}\n"
                f"   {desc}"
            )

        prompt = PLAN_DAY_PROMPT.format(
            destination=preferences.destination,
            daily_budget=budget_per_day,
            total_budget=preferences.budget,
            people=preferences.people,
            style=preferences.style or "not specified",
            categories=preferences.categories or "all",
            implicit=preferences.implicit_preferences or "none stated",
            notes=preferences.planning_notes or "none",
            places="\n".join(places_text),
        )

        langfuse = self._get_langfuse()
        input_data = {
            "day_number": day_number,
            "total_days": total_days,
            "destination": preferences.destination,
            "daily_budget": budget_per_day,
            "style": preferences.style,
            "places_count": len(places),
        }

        if langfuse:
            with langfuse.start_as_current_observation(
                name=f"plan-day-{day_number}",
                input=input_data,
                metadata={
                    "model": self.model,
                    "temperature": self.temperature,
                },
            ) as observation:
                response = await self._call_llm(
                    system_prompt=prompt,
                    user_message=f"Plan day {day_number} of {total_days}.",
                )
                result = json.loads(response)
                observation.output = result
                return result
        else:
            return json.loads(
                await self._call_llm(
                    system_prompt=prompt,
                    user_message=f"Plan day {day_number} of {total_days}.",
                )
            )

    async def critique_day(
        self,
        day_plan: dict[str, Any],
        preferences,
        hard_violations: list[str],
    ) -> dict[str, Any]:
        """Critique the day's plan and suggest improvements."""
        places_text = []
        for i, p in enumerate(day_plan.get("places", [])):
            cost = p.get("cost_estimate", 0)
            duration = p.get("duration_hours", 1)
            cat = p.get("category", "unknown")
            places_text.append(
                f"{i+1}. {p['name']} ({cat})\n"
                f"   Cost: {cost} JPY, Duration: {duration}h"
            )

        violations_str = (
            "\n".join(f"- {v}" for v in hard_violations)
            if hard_violations
            else "None"
        )

        prompt = CRITIQUE_DAY_PROMPT.format(
            destination=preferences.destination,
            style=preferences.style or "not specified",
            implicit=preferences.implicit_preferences or "none",
            notes=preferences.planning_notes or "none",
            daily_budget=preferences.daily_budget,
            violations=violations_str,
            places="\n".join(places_text),
        )

        langfuse = self._get_langfuse()
        input_data = {
            "destination": preferences.destination,
            "hard_violations": hard_violations,
            "places_count": len(day_plan.get("places", [])),
        }

        if langfuse:
            with langfuse.start_as_current_observation(
                name="critique-day",
                input=input_data,
                metadata={
                    "model": self.model,
                    "temperature": self.temperature,
                },
            ) as observation:
                response = await self._call_llm(
                    system_prompt=prompt,
                    user_message="Review this day's plan.",
                )
                result = json.loads(response)
                observation.output = result
                return result
        else:
            return json.loads(
                await self._call_llm(
                    system_prompt=prompt,
                    user_message="Review this day's plan.",
                )
            )

    async def should_continue(
        self,
        completed_days: list[dict[str, Any]],
        preferences,
    ) -> dict[str, Any]:
        """Decide if the itinerary is complete and satisfying."""
        days_summary = []
        for i, day in enumerate(completed_days):
            places = [p["name"] for p in day.get("places", [])]
            short_list = ", ".join(places[:3])
            ellipsis = "..." if len(places) > 3 else ""
            days_summary.append(f"Day {i+1}: {short_list}{ellipsis}")

        prompt = SHOULD_CONTINUE_PROMPT.format(
            destination=preferences.destination,
            days=preferences.days,
            style=preferences.style or "not specified",
            implicit=preferences.implicit_preferences or "none",
            days_list="\n".join(days_summary),
        )

        langfuse = self._get_langfuse()
        input_data = {
            "destination": preferences.destination,
            "total_days": preferences.days,
            "completed_days": len(completed_days),
        }

        if langfuse:
            with langfuse.start_as_current_observation(
                name="should-continue",
                input=input_data,
                metadata={
                    "model": self.model,
                    "temperature": self.temperature,
                },
            ) as observation:
                response = await self._call_llm(
                    system_prompt=prompt,
                    user_message="Should we finalize this itinerary?",
                )
                result = json.loads(response)
                observation.output = result
                return result
        else:
            return json.loads(
                await self._call_llm(
                    system_prompt=prompt,
                    user_message="Should we finalize this itinerary?",
                )
            )

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Make the actual LLM API call."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=self.temperature,
        )
        return response.choices[0].message.content


# Singleton instance
llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create the LLM client singleton."""
    global llm_client
    if llm_client is None:
        llm_client = LLMClient()
    return llm_client
