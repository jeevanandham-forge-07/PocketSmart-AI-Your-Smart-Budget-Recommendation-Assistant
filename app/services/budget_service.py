import math
from typing import List, Tuple, Dict
from app.models.schemas import RecommendationItem, CategoryAllocation


class BudgetEngine:
    """
    Deterministic Python Financial Engine for Budget Validation,
    Arithmetic Verification, and Category Allocations.
    """

    @staticmethod
    def calculate_totals(items: List[RecommendationItem]) -> Tuple[List[RecommendationItem], float]:
        """Calculates exact subtotals and total estimated spending from items"""
        clean_items: List[RecommendationItem] = []
        for it in items:
            qty = max(1, int(it.quantity))
            price = max(0.0, round(float(it.estimated_price), 2))
            it.quantity = qty
            it.estimated_price = price
            it.subtotal = round(price * qty, 2)
            clean_items.append(it)
        
        total = round(sum(i.subtotal for i in clean_items), 2)
        return clean_items, total

    @staticmethod
    def validate_budget(
        user_budget: float,
        items: List[RecommendationItem],
        currency: str = "INR"
    ) -> Tuple[List[RecommendationItem], List[CategoryAllocation], float, float, List[str]]:
        """
        Validates AI items against the user budget.
        Calculates:
            subtotal = estimated_price * quantity
            total_estimated_spending = sum(subtotals)
            remaining_budget = user_budget - total_estimated_spending
        Returns:
            Tuple: (clean_items, category_allocations, total_cost, remaining_budget, warnings)
        """
        warnings: List[str] = []
        user_budget = max(0.0, round(float(user_budget), 2))

        if not items:
            return [], [], 0.0, user_budget, ["No recommendation items were generated."]

        # 1. Clean & compute subtotals deterministically
        clean_items, total_cost = BudgetEngine.calculate_totals(items)

        # 2. Check budget edge cases
        if user_budget <= 0:
            for it in clean_items:
                it.estimated_price = 0.0
                it.subtotal = 0.0
            return clean_items, [], 0.0, 0.0, ["User budget must be greater than zero."]

        # 3. Check if total exceeds budget
        if total_cost > user_budget:
            warnings.append(
                f"Total estimated cost ({currency} {total_cost:,.2f}) exceeded target budget ({currency} {user_budget:,.2f})."
            )

        # 4. Strict deterministic remaining calculation
        remaining_budget = max(0.0, round(user_budget - total_cost, 2))

        # 5. Build dynamic category breakdown
        category_sums: Dict[str, float] = {}
        for it in clean_items:
            cat = it.category.strip() or "General"
            category_sums[cat] = category_sums.get(cat, 0.0) + it.subtotal

        allocations: List[CategoryAllocation] = []
        for cat, amt in sorted(category_sums.items(), key=lambda x: x[1], reverse=True):
            pct = round((amt / total_cost * 100), 1) if total_cost > 0 else 0.0
            allocations.append(
                CategoryAllocation(
                    category=cat,
                    allocated_amount=round(amt, 2),
                    percentage=pct,
                    description=f"Estimated allocation for {cat}"
                )
            )

        return clean_items, allocations, total_cost, remaining_budget, warnings

    @classmethod
    def validate_and_rebalance(
        cls,
        user_budget: float,
        items: List[RecommendationItem],
        currency: str = "INR"
    ) -> Tuple[List[RecommendationItem], List[CategoryAllocation], float, float, List[str]]:
        """Backwards-compatible alias for validate_budget"""
        return cls.validate_budget(user_budget, items, currency)


budget_engine = BudgetEngine()
