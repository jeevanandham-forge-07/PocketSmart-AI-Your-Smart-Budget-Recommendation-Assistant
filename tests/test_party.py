import pytest
from app.models.schemas import PartyPlannerInput
from app.services.recommendation_service import recommendation_service


def test_party_planner_scenario():
    input_data = PartyPlannerInput(
        budget=75000.0,
        currency="INR",
        guest_count=50,
        event_type="Birthday Party",
        city_location="Chennai",
        venue_required=True,
        catering_required=True,
        decoration_required=True,
        entertainment_required=True,
        cake_required=True,
        food_preference="Multi-Cuisine"
    )

    plan = recommendation_service.process_party_plan(input_data=input_data)

    assert plan is not None
    assert plan.planner_type == "party"
    assert plan.original_budget == 75000.0
    assert plan.total_estimated_cost <= 75000.0
    assert plan.remaining_budget >= 0.0
    assert len(plan.items) > 0
    assert len(plan.category_breakdown) > 0

    # Ensure search links contain party providers like Zomato, Swiggy, OYO
    all_provider_names = []
    for item in plan.items:
        all_provider_names.extend(item.platform_links.keys())

    assert any(p in all_provider_names for p in ["Zomato", "Swiggy", "OYO", "Amazon"])


def test_party_planner_invalid_guests():
    with pytest.raises(ValueError):
        PartyPlannerInput(budget=50000, guest_count=0)
