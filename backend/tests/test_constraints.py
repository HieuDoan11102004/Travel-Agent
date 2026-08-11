"""Tests for constraint validation."""

import pytest

from app.constraints.types import (
    Constraint, ConstraintType, HARD_CONSTRAINTS,
    check_daily_cost, check_daily_hours, check_travel_time
)
from app.constraints.validator import ConstraintValidator
from app.models.day_plan import DayPlan
from app.models.place import Place, Location
from app.models.preferences import UserPreferences


def make_place(
    cost: int = 1000,
    duration: float = 2.0,
    category: str = "attraction"
) -> Place:
    """Helper to create a test place."""
    return Place(
        id=f"test-{cost}",
        name="Test Place",
        category=category,
        subcategory="test",
        location=Location(lat=35.7, lng=139.7),
        cost_estimate=cost,
        duration_hours=duration,
        popularity="medium",
        rating=4.0,
    )


def make_preferences(days: int = 3, budget: int = 100000) -> UserPreferences:
    """Helper to create test preferences."""
    return UserPreferences(
        destination="Tokyo",
        days=days,
        people=2,
        budget=budget,
    )


def make_day_plan(places: list[Place], travel_minutes: int = 30) -> DayPlan:
    """Helper to create a test day plan."""
    day = DayPlan(
        date="2024-03-15",
        places=places,
    )
    day.calculate_totals()
    day.travel_time_minutes = travel_minutes
    return day


class TestHardConstraints:
    def test_check_daily_cost_pass(self):
        prefs = make_preferences(budget=90000)  # Daily limit = 33000
        day = make_day_plan([make_place(cost=30000)])
        passed, msg = check_daily_cost(day, prefs)
        assert passed is True
        assert msg is None

    def test_check_daily_cost_fail(self):
        prefs = make_preferences(budget=90000)  # Daily limit = 33000
        day = make_day_plan([make_place(cost=50000)])
        passed, msg = check_daily_cost(day, prefs)
        assert passed is False
        assert "exceeds" in msg

    def test_check_daily_hours_pass(self):
        prefs = make_preferences()
        day = make_day_plan([make_place(duration=5.0), make_place(duration=4.0)])
        passed, msg = check_daily_hours(day, prefs)
        assert passed is True

    def test_check_daily_hours_fail(self):
        prefs = make_preferences()
        day = make_day_plan([make_place(duration=6.0), make_place(duration=5.0)])
        passed, msg = check_daily_hours(day, prefs)
        assert passed is False
        assert "exceeds" in msg

    def test_check_travel_time_pass(self):
        prefs = make_preferences()
        day = make_day_plan([make_place() for _ in range(3)], travel_minutes=45)
        passed, msg = check_travel_time(day, prefs)
        assert passed is True

    def test_check_travel_time_fail(self):
        prefs = make_preferences()
        day = make_day_plan([make_place() for _ in range(5)], travel_minutes=120)
        passed, msg = check_travel_time(day, prefs)
        assert passed is False


class TestConstraintValidator:
    def test_validate_day_plan_pass(self):
        validator = ConstraintValidator()
        prefs = make_preferences(budget=100000)
        day = make_day_plan([make_place(cost=30000, duration=5.0)], travel_minutes=30)

        passed, violations = validator.validate_day_plan(day, prefs)
        assert passed is True
        assert violations == []

    def test_validate_day_plan_fail_multiple(self):
        validator = ConstraintValidator()
        prefs = make_preferences(budget=100000)
        day = make_day_plan([
            make_place(cost=60000, duration=6.0),
            make_place(cost=50000, duration=5.0)
        ], travel_minutes=120)

        passed, violations = validator.validate_day_plan(day, prefs)
        assert passed is False
        assert len(violations) >= 1

    def test_validate_itinerary(self):
        validator = ConstraintValidator()
        prefs = make_preferences(budget=100000)

        day1 = make_day_plan([make_place(cost=30000)], travel_minutes=20)
        day2 = make_day_plan([make_place(cost=80000)], travel_minutes=20)  # Over budget

        passed, violations = validator.validate_itinerary([day1, day2], prefs)
        assert passed is False
        assert len(violations) >= 1

    def test_get_constraint_status(self):
        validator = ConstraintValidator()
        prefs = make_preferences()
        day = make_day_plan([make_place()])

        status = validator.get_constraint_status(day, prefs)
        assert "all_passed" in status
        assert "constraints" in status
        assert len(status["constraints"]) >= 3
