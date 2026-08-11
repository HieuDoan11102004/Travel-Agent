"""Reranker for improving search result quality."""

from typing import Literal

from app.models.place import Place
from app.models.preferences import UserPreferences


class Reranker:
    """Reranks search results based on preference compatibility."""

    def __init__(self):
        self.category_weights = {
            "attraction": 1.0,
            "restaurant": 1.0,
            "hotel": 0.8,
            "shopping": 0.7,
            "transport": 0.5,
        }

    def rerank(
        self,
        results: list[dict],
        preferences: UserPreferences | None = None,
        balance_categories: bool = True,
    ) -> list[dict]:
        """Rerank results based on preferences.

        Args:
            results: List of search results with place and score
            preferences: User preferences for context-aware reranking
            balance_categories: Whether to balance category distribution

        Returns:
            Reranked results with preference_score added
        """
        if not results:
            return results

        scored_results = []
        category_counts: dict[str, int] = {}

        for result in results:
            place = result["place"]
            original_score = result.get("rrf_score", result.get("score", 0))

            # Calculate preference score
            pref_score = self._calculate_preference_score(place, preferences)

            # Calculate category balance score
            balance_score = self._calculate_balance_score(
                place, category_counts, balance_categories
            )

            # Final score: weighted combination
            final_score = (
                original_score * 0.5 +
                pref_score * 0.3 +
                balance_score * 0.2
            )

            scored_results.append({
                **result,
                "preference_score": pref_score,
                "balance_score": balance_score,
                "final_score": final_score,
            })

            # Update category counts
            cat = place.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Sort by final score
        scored_results.sort(key=lambda x: x["final_score"], reverse=True)

        return scored_results

    def _calculate_preference_score(
        self,
        place: dict,
        preferences: UserPreferences | None,
    ) -> float:
        """Calculate preference compatibility score."""
        if not preferences:
            return 0.5

        score = 0.0
        weight = 0.0

        # Category preference
        if preferences.categories:
            weight += 1.0
            if place.get("category") in preferences.categories:
                score += 1.0

        # Style preference (mapped to relevant categories)
        if preferences.style:
            weight += 0.5
            style_categories = self._style_to_categories(preferences.style)
            if place.get("category") in style_categories:
                score += 1.0

        # Mobility affects acceptable transport needs
        if preferences.mobility == "walking":
            weight += 0.3
            # Walking-friendly places get boost
            if place.get("category") in ["attraction", "restaurant"]:
                score += 0.5

        return score / weight if weight > 0 else 0.5

    def _style_to_categories(self, style: str) -> list[str]:
        """Map travel style to relevant categories."""
        style_map = {
            "cultural": ["attraction"],
            "foodie": ["restaurant"],
            "nature": ["attraction"],
            "shopping": ["shopping", "attraction"],
            "nightlife": ["restaurant", "attraction"],
        }
        return style_map.get(style.lower(), ["attraction", "restaurant"])

    def _calculate_balance_score(
        self,
        place: dict,
        category_counts: dict[str, int],
        balance: bool,
    ) -> float:
        """Calculate category diversity score.

        Rewards including underrepresented categories.
        """
        if not balance:
            return 0.5

        category = place.get("category", "unknown")
        count = category_counts.get(category, 0)

        # Fewer occurrences = higher bonus (up to 0.5 bonus)
        if count == 0:
            return 1.0
        elif count == 1:
            return 0.8
        elif count == 2:
            return 0.6
        else:
            return 0.4
