"""Constraint validator for day plans and itineraries."""


from app.constraints.types import Constraint, get_hard_constraints
from app.models.day_plan import DayPlan
from app.models.preferences import UserPreferences


class ConstraintValidator:
    """Validates day plans against constraints."""

    def __init__(self, hard_constraints: list[Constraint] | None = None):
        self.hard_constraints = hard_constraints or get_hard_constraints()

    def validate_day_plan(
        self,
        day_plan: DayPlan,
        preferences: UserPreferences,
    ) -> tuple[bool, list[str]]:
        """Validate a single day plan.

        Returns:
            (all_passed, list_of_violations)
        """
        violations = []

        for constraint in self.hard_constraints:
            passed, message = constraint.evaluate(day_plan, preferences)
            if not passed and message:
                violations.append(message)

        return len(violations) == 0, violations

    def validate_itinerary(
        self,
        day_plans: list[DayPlan],
        preferences: UserPreferences,
    ) -> tuple[bool, list[str]]:
        """Validate all day plans in an itinerary."""
        all_violations = []

        for i, day_plan in enumerate(day_plans):
            passed, violations = self.validate_day_plan(day_plan, preferences)
            if violations:
                day_label = day_plan.date or f"Day {i + 1}"
                all_violations.extend([f"{day_label}: {v}" for v in violations])

        return len(all_violations) == 0, all_violations

    def get_constraint_status(
        self,
        day_plan: DayPlan,
        preferences: UserPreferences,
    ) -> dict:
        """Get detailed constraint status for a day plan."""
        results = []
        for constraint in self.hard_constraints:
            passed, message = constraint.evaluate(day_plan, preferences)
            results.append({
                "name": constraint.name,
                "description": constraint.description,
                "passed": passed,
                "message": message,
            })
        return {
            "all_passed": all(r["passed"] for r in results),
            "constraints": results,
        }
