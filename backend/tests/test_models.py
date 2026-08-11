import pytest
from pydantic import ValidationError

from app.models.place import Place, Location
from app.models.day_plan import DayPlan
from app.models.itinerary import Itinerary
from app.models.preferences import UserPreferences


class TestPlace:
    def test_place_valid(self):
        place = Place(
            id="test-1",
            name="Test Temple",
            category="attraction",
            subcategory="shrine",
            location={"lat": 35.7, "lng": 139.7},
            cost_estimate=500,
            duration_hours=2.0,
            popularity="high",
            rating=4.5,
        )
        assert place.id == "test-1"
        assert place.name == "Test Temple"
        assert place.location.lat == 35.7

    def test_place_invalid_lat(self):
        with pytest.raises(ValidationError):
            Place(
                id="test-1",
                name="Test",
                category="attraction",
                subcategory="test",
                location={"lat": 100, "lng": 139.7},  # Invalid lat
                cost_estimate=0,
                duration_hours=1.0,
                popularity="medium",
                rating=4.0,
            )

    def test_place_invalid_rating(self):
        with pytest.raises(ValidationError):
            Place(
                id="test-1",
                name="Test",
                category="attraction",
                subcategory="test",
                location={"lat": 35.7, "lng": 139.7},
                cost_estimate=0,
                duration_hours=1.0,
                popularity="medium",
                rating=6.0,  # Invalid rating > 5
            )


class TestUserPreferences:
    def test_preferences_valid(self):
        prefs = UserPreferences(
            destination="Tokyo",
            days=3,
            people=2,
            budget=100000,
        )
        assert prefs.destination == "Tokyo"
        assert prefs.daily_budget == 33333

    def test_preferences_with_style(self):
        prefs = UserPreferences(
            destination="Tokyo",
            days=5,
            people=1,
            budget=200000,
            style="foodie",
            mobility="walking",
        )
        assert prefs.style == "foodie"
        assert prefs.mobility == "walking"

    def test_preferences_invalid_days(self):
        with pytest.raises(ValidationError):
            UserPreferences(
                destination="Tokyo",
                days=0,  # Must be >= 1
                people=1,
                budget=50000,
            )


class TestDayPlan:
    def test_day_plan_empty(self):
        day = DayPlan(date="2024-03-15")
        assert day.total_cost == 0
        assert day.total_hours == 0

    def test_day_plan_calculate_totals(self):
        place1 = Place(
            id="p1",
            name="Temple",
            category="attraction",
            subcategory="shrine",
            location={"lat": 35.7, "lng": 139.7},
            cost_estimate=1000,
            duration_hours=2.0,
            popularity="high",
            rating=4.5,
        )
        place2 = Place(
            id="p2",
            name="Restaurant",
            category="restaurant",
            subcategory="sushi",
            location={"lat": 35.71, "lng": 139.71},
            cost_estimate=3000,
            duration_hours=1.5,
            popularity="medium",
            rating=4.2,
        )
        day = DayPlan(date="2024-03-15", places=[place1, place2])
        day.calculate_totals()
        assert day.total_cost == 4000
        assert day.total_hours == 3.5


class TestItinerary:
    def test_itinerary_empty(self):
        itinerary = Itinerary()
        assert itinerary.total_cost == 0
        assert itinerary.constraints_satisfied is True
        assert itinerary.violations == []

    def test_itinerary_with_violations(self):
        itinerary = Itinerary(
            constraints_satisfied=False,
            violations=["Daily cost exceeded budget"],
        )
        assert itinerary.constraints_satisfied is False
        assert len(itinerary.violations) == 1
