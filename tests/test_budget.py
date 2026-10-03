import pytest
from app.services.budget_service import budget_engine
from app.models.schemas import RecommendationItem


def test_budget_within_limit():
    items = [
        RecommendationItem(
            item_name="Modern Table",
            category="Furniture",
            description="Wooden table",
            estimated_price=10000.0,
            quantity=1,
            reason="Good fit",
            search_term="table"
        ),
        RecommendationItem(
            item_name="Chair",
            category="Furniture",
            description="Comfort chair",
            estimated_price=2500.0,
            quantity=4,
            reason="Seating",
            search_term="chair"
        )
    ]
    # Total = 10000*1 + 2500*4 = 20000
    user_budget = 25000.0
    clean_items, allocations, total_cost, remaining, warnings = budget_engine.validate_and_rebalance(
        user_budget=user_budget,
        items=items
    )

    assert total_cost == 20000.0
    assert remaining == 5000.0
    assert total_cost <= user_budget
    assert len(warnings) == 0
    assert len(allocations) == 1
    assert allocations[0].category == "Furniture"
    assert allocations[0].allocated_amount == 20000.0
    assert allocations[0].percentage == 100.0


def test_budget_overflow_detection():
    # User budget: 50,000, AI items total: 100,000
    items = [
        RecommendationItem(
            item_name="Luxury Sofa",
            category="Furniture",
            description="Leather sofa",
            estimated_price=60000.0,
            quantity=1,
            reason="Centerpiece",
            search_term="sofa"
        ),
        RecommendationItem(
            item_name="Designer Lamp",
            category="Lighting",
            description="Floor lamp",
            estimated_price=40000.0,
            quantity=1,
            reason="Lighting",
            search_term="lamp"
        )
    ]
    user_budget = 50000.0
    clean_items, total = budget_engine.calculate_totals(items)
    assert total == 100000.0
    assert total > user_budget

    clean_items, allocations, total_cost, remaining, warnings = budget_engine.validate_budget(
        user_budget=user_budget,
        items=items
    )

    # Verifies that Python does not blindly scale down prices, but reports the overflow warning
    assert total_cost == 100000.0
    assert remaining == 0.0
    assert len(warnings) > 0
    assert "exceeded" in warnings[0].lower()


def test_empty_items_budget():
    clean_items, allocations, total_cost, remaining, warnings = budget_engine.validate_and_rebalance(
        user_budget=10000.0,
        items=[]
    )
    assert total_cost == 0.0
    assert remaining == 10000.0
    assert len(clean_items) == 0


def test_zero_or_negative_budget():
    items = [
        RecommendationItem(
            item_name="Item 1",
            category="Decor",
            description="Test",
            estimated_price=500.0,
            quantity=1,
            reason="Test",
            search_term="test"
        )
    ]
    clean_items, allocations, total_cost, remaining, warnings = budget_engine.validate_and_rebalance(
        user_budget=0.0,
        items=items
    )
    assert total_cost <= 0.0
    assert remaining == 0.0
