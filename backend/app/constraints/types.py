"""Constraint types and rules."""

from enum import Enum


class ConstraintType(str, Enum):
    """Types of constraints."""

    HARD = "hard"  # Must satisfy or list as violation
    SOFT = "soft"  # Optimize but not required


class Constraint:
    """Represents a constraint rule."""

    def __init__(
        self,
        name: str,
        description: str,
        constraint_type: ConstraintType,
        check_func: callable,
    ):
        self.name = name
        self.description = description
        self.constraint_type = constraint_type
        self.check_func = check_func

    def evaluate(self, day_plan, preferences) -> tuple[bool, str | None]:
        """Evaluate the constraint. Returns (passed, violation_message)."""
        return self.check_func(day_plan, preferences)


# Default constraints
MAX_DAILY_HOURS = 10.0
MAX_TRAVEL_TIME_MINUTES = 90
DAILY_BUDGET_MULTIPLIER = 1.1


def check_daily_cost(day_plan, preferences) -> tuple[bool, str | None]:
    """Check daily cost doesn't exceed budget."""
    daily_limit = (preferences.budget // preferences.days) * DAILY_BUDGET_MULTIPLIER
    if day_plan.total_cost > daily_limit:
        return False, f"Daily cost ¥{day_plan.total_cost:,} exceeds limit ¥{int(daily_limit):,}"
    return True, None


def check_daily_hours(day_plan, preferences) -> tuple[bool, str | None]:
    """Check daily hours don't exceed limit."""
    if day_plan.total_hours > MAX_DAILY_HOURS:
        return False, f"Daily hours {day_plan.total_hours:.1f} exceeds {MAX_DAILY_HOURS}h limit"
    return True, None


def check_travel_time(day_plan, preferences) -> tuple[bool, str | None]:
    """Check travel time doesn't exceed limit."""
    if day_plan.travel_time_minutes > MAX_TRAVEL_TIME_MINUTES:
        return False, f"Travel time {day_plan.travel_time_minutes}min exceeds {MAX_TRAVEL_TIME_MINUTES}min limit"
    return True, None


def check_place_availability(day_plan, preferences) -> tuple[bool, str | None]:
    """Check all places are available on the visit date."""
    # Simplified check - in production would check actual hours
    return True, None


# Hard constraints
HARD_CONSTRAINTS = [
    Constraint(
        name="daily_cost",
        description=f"Daily cost ≤ budget/days × {DAILY_BUDGET_MULTIPLIER}",
        constraint_type=ConstraintType.HARD,
        check_func=check_daily_cost,
    ),
    Constraint(
        name="daily_hours",
        description=f"Daily hours ≤ {MAX_DAILY_HOURS}h",
        constraint_type=ConstraintType.HARD,
        check_func=check_daily_hours,
    ),
    Constraint(
        name="travel_time",
        description=f"Travel time ≤ {MAX_TRAVEL_TIME_MINUTES}min",
        constraint_type=ConstraintType.HARD,
        check_func=check_travel_time,
    ),
    Constraint(
        name="place_availability",
        description="All places open on visit date",
        constraint_type=ConstraintType.HARD,
        check_func=check_place_availability,
    ),
]


def get_hard_constraints() -> list[Constraint]:
    """Get all hard constraints."""
    return HARD_CONSTRAINTS
