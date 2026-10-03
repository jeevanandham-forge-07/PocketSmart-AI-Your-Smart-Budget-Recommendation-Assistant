import io
import pytest
from unittest.mock import patch
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    PartyPlannerInput,
    HomePlannerInput,
    JewelryPlannerInput
)
from app.services.recommendation_service import recommendation_service
from app.services.gemini_service import gemini_service, GeminiServiceError

client = TestClient(app, follow_redirects=True)


# ============================================================
# PHASE 10: ANTI-FAKE TEST
# ============================================================
def test_anti_fake_party_allocations():
    """
    Proves recommendations are NOT fixed percentages.
    Runs 3 materially different scenarios:
      A: 50 guests, birthday, venue+catering+decor+entertainment
      B: 10 guests, small family birthday, venue=NO, entertainment=NO
      C: 100 guests, corporate celebration
    """
    # Test A: Standard 50-guest celebration with all services
    input_a = PartyPlannerInput(
        budget=85000.0,
        currency="INR",
        guest_count=50,
        event_type="Birthday",
        city_location="Chennai",
        catering_required=True,
        venue_required=True,
        decoration_required=True,
        entertainment_required=True,
        cake_required=True,
        food_preference="Multi-Cuisine"
    )
    plan_a = recommendation_service.process_party_plan(input_a)
    assert plan_a.response_source == "GEMINI"
    assert plan_a.is_ai_generated is True
    assert plan_a.total_estimated_cost <= 85000.0
    assert plan_a.remaining_budget >= 0.0

    # Test B: 10 guests, family gathering, NO venue, NO entertainment
    input_b = PartyPlannerInput(
        budget=85000.0,
        currency="INR",
        guest_count=10,
        event_type="Small family birthday",
        city_location="Chennai",
        catering_required=True,
        venue_required=False,
        decoration_required=True,
        entertainment_required=False,
        cake_required=True,
        food_preference="South Indian"
    )
    plan_b = recommendation_service.process_party_plan(input_b)
    assert plan_b.response_source == "GEMINI"
    assert plan_b.is_ai_generated is True
    assert plan_b.total_estimated_cost <= 85000.0

    # Ensure Test B did NOT blindly allocate Venue or Entertainment costs
    has_venue_b = any("venue" in item.category.lower() or "hall" in item.item_name.lower() for item in plan_b.items)
    # The prompt explicitly instructed not to recommend venue if venue_required is False
    assert not has_venue_b, "Test B should not allocate a venue when venue_required is False"

    # Test C: 100 guests, corporate event
    input_c = PartyPlannerInput(
        budget=85000.0,
        currency="INR",
        guest_count=100,
        event_type="Corporate celebration",
        city_location="Chennai",
        catering_required=True,
        venue_required=True,
        decoration_required=False,
        entertainment_required=True,
        cake_required=False,
        food_preference="Continental & Indian"
    )
    plan_c = recommendation_service.process_party_plan(input_c)
    assert plan_c.response_source == "GEMINI"
    assert plan_c.total_estimated_cost <= 85000.0

    # PROOF: The allocations must be materially different across scenarios
    # In the old code: Catering was ALWAYS exactly 45% (38,250), Venue ALWAYS 25% (21,250)
    # Now: Categories and amounts reflect actual user requirements dynamically
    allocs_a = {a.category: a.percentage for a in plan_a.category_breakdown}
    allocs_b = {a.category: a.percentage for a in plan_b.category_breakdown}
    allocs_c = {a.category: a.percentage for a in plan_c.category_breakdown}

    print("\n--- ANTI-FAKE ALLOCATION COMPARISON ---")
    print("Plan A allocations:", allocs_a)
    print("Plan B allocations:", allocs_b)
    print("Plan C allocations:", allocs_c)

    # Validate that B does not match A (Venue is 0% in B, catering per-head reflects 10 pax)
    assert allocs_a != allocs_b, "Allocations between Test A and Test B should not be identical!"
    assert allocs_b != allocs_c, "Allocations between Test B and Test C should not be identical!"


# ============================================================
# PHASE 11: GEMINI FAILURE TEST
# ============================================================
def test_gemini_failure_raises_error_and_no_fake_data():
    """
    Simulates Gemini API failure and proves the application does NOT return
    fake mock recommendations or pretend to be AI.
    """
    with patch.object(gemini_service, "_call_structured_model", side_effect=GeminiServiceError("AI recommendation unavailable. Please try again.")):
        # 1. Direct service call must raise GeminiServiceError
        input_data = PartyPlannerInput(
            budget=50000.0,
            currency="INR",
            guest_count=20,
            event_type="Birthday",
            city_location="Chennai"
        )
        with pytest.raises(GeminiServiceError) as exc_info:
            recommendation_service.process_party_plan(input_data)
        assert "AI recommendation unavailable" in str(exc_info.value)

        # 2. Web form submission must display the explicit error message in UI
        response = client.post(
            "/generate-party",
            data={
                "budget": "50000",
                "currency": "INR",
                "guest_count": "20",
                "event_type": "Birthday",
                "city_location": "Chennai",
                "venue_required": "true",
                "catering_required": "true"
            }
        )
        assert response.status_code == 503
        assert "AI recommendation unavailable" in response.text
        # Assert that it does NOT show a mock recommendation card
        assert "Curated Recommendations" not in response.text
        assert "Multi-Course Buffet Catering" not in response.text


# ============================================================
# PHASE 12: AUDIT HOME & JEWELRY PLANNERS
# ============================================================
def test_home_planner_calls_gemini_and_validates():
    """Verifies Home Planner calls Gemini and Python validates math"""
    input_data = HomePlannerInput(
        budget=120000.0,
        currency="INR",
        living_room=True,
        bedroom_count=2,
        kitchen=True,
        dining_room=True,
        lights_count=8,
        fans_count=3,
        dining_table_count=1,
        furniture_requirements="Teakwood dining table and modular sofa",
        decor_requirements="Minimalist wall sconces and geometric rug",
        preferred_style="Scandinavian Minimalist",
        color_preferences="Sage Green and White Oak"
    )
    plan = recommendation_service.process_home_plan(input_data)
    assert plan.planner_type == "home"
    assert plan.response_source == "GEMINI"
    assert plan.is_ai_generated is True
    assert plan.total_estimated_cost <= 120000.0
    assert plan.remaining_budget == pytest.approx(120000.0 - plan.total_estimated_cost, 0.01)
    assert len(plan.items) > 0


def test_jewelry_planner_text_calls_gemini():
    """Verifies Jewelry Planner without image calls Gemini text generation"""
    input_data = JewelryPlannerInput(
        budget=25000.0,
        currency="INR",
        occasion="Engagement",
        jewelry_type="Necklace and Earrings",
        style_preference="Contemporary Diamond Look",
        metal_preference="Rose Gold Plated",
        color_preference="Blush Pink"
    )
    plan = recommendation_service.process_jewelry_plan(input_data)
    assert plan.planner_type == "jewelry"
    assert plan.response_source == "GEMINI"
    assert plan.is_ai_generated is True
    assert plan.total_estimated_cost <= 25000.0
    assert plan.remaining_budget == pytest.approx(25000.0 - plan.total_estimated_cost, 0.01)


def test_jewelry_planner_with_image_calls_multimodal(tmp_path):
    """Verifies Jewelry Planner with image triggers Gemini multimodal visual analysis"""
    # Create test garment image
    test_img = Image.new("RGB", (200, 200), color=(147, 51, 234))  # Royal Purple
    test_img_path = tmp_path / "purple_outfit.png"
    test_img.save(test_img_path)

    input_data = JewelryPlannerInput(
        budget=35000.0,
        currency="INR",
        occasion="Reception Gala",
        jewelry_type="Complete Set",
        style_preference="Kundan & Pearls",
        metal_preference="Gold Plated",
        color_preference="Purple and Gold"
    )

    plan = recommendation_service.process_jewelry_plan(
        input_data=input_data,
        image_path=test_img_path,
        image_url="/static/uploads/purple_outfit.png"
    )

    assert plan.planner_type == "jewelry"
    assert plan.response_source == "GEMINI"
    assert plan.is_ai_generated is True
    assert plan.outfit_image_url == "/static/uploads/purple_outfit.png"
    assert plan.outfit_analysis is not None
    assert plan.total_estimated_cost <= 35000.0
