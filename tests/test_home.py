import pytest
from app.models.schemas import HomePlannerInput
from app.services.recommendation_service import recommendation_service


def test_home_planner_scenario():
    input_data = HomePlannerInput(
        budget=100000.0,
        currency="INR",
        living_room=True,
        bedroom_count=2,
        kitchen=True,
        dining_room=True,
        lights_count=10,
        fans_count=3,
        dining_table_count=1,
        furniture_requirements="Sofa and beds",
        decor_requirements="Wall art",
        preferred_style="Modern",
        color_preferences="Warm Neutral"
    )

    plan = recommendation_service.process_home_plan(input_data=input_data)

    assert plan is not None
    assert plan.planner_type == "home"
    assert plan.original_budget == 100000.0
    assert plan.total_estimated_cost <= 100000.0
    assert plan.remaining_budget >= 0.0
    assert len(plan.items) > 0

    # Verify each item structure and links
    for item in plan.items:
        assert item.estimated_price > 0
        assert item.quantity >= 1
        assert item.subtotal == pytest.approx(item.estimated_price * item.quantity, 0.01)
        assert item.platform_links is not None
        assert len(item.platform_links) > 0
        # Check that search URLs are valid strings
        for name, url in item.platform_links.items():
            assert url.startswith("http://") or url.startswith("https://")


def test_home_planner_validation_limits():
    with pytest.raises(ValueError):
        HomePlannerInput(budget=-500)

    with pytest.raises(ValueError):
        HomePlannerInput(budget=0)
