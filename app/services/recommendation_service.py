import json
import logging
from pathlib import Path
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.recommendation import RecommendationRecord
from app.models.schemas import (
    HomePlannerInput,
    PartyPlannerInput,
    JewelryPlannerInput,
    RecommendationItem,
    CategoryAllocation,
    OutfitAnalysis,
    PlannerResponseData,
    GeminiPlanOutput,
    GeminiJewelryPlanOutput
)
from app.services.gemini_service import gemini_service, GeminiServiceError
from app.services.budget_service import budget_engine
from app.services.product_provider import product_link_service

logger = logging.getLogger("pocketsmart.recommendation")


class RecommendationService:
    """Master orchestrator for Gemini generation, Python budget validation, and persistence"""

    def process_home_plan(
        self,
        input_data: HomePlannerInput,
        user: Optional[User] = None,
        db: Optional[Session] = None
    ) -> PlannerResponseData:
        # 1. AI generation
        raw_plan, actual_model = gemini_service.generate_home_plan(input_data)

        # 2. Convert recommendations to RecommendationItem schema
        raw_items = self._convert_items(raw_plan.recommendations, default_cat="Furniture")

        # 3. Python arithmetic verification & revision loop (Phase 6)
        clean_items, total = budget_engine.calculate_totals(raw_items)
        max_retries = 2
        retries = 0

        while total > input_data.budget and retries < max_retries:
            retries += 1
            excess = round(total - input_data.budget, 2)
            logger.info(f"Home plan exceeded budget by {excess}. Attempting Gemini revision {retries}/{max_retries}...")
            raw_plan, actual_model = gemini_service.revise_plan_for_budget(
                original_budget=input_data.budget,
                currency=input_data.currency,
                generated_plan=raw_plan,
                calculated_total=total,
                excess_amount=excess,
                planner_name="HOME"
            )
            raw_items = self._convert_items(raw_plan.recommendations, default_cat="Furniture")
            clean_items, total = budget_engine.calculate_totals(raw_items)

        if total > input_data.budget:
            print("Response source: ERROR")
            print("Budget validation: FAILED")
            print("=" * 50)
            raise GeminiServiceError(
                f"Generated home plan exceeded target budget ({input_data.currency} {input_data.budget:,.2f}) after {retries} revisions."
            )

        # 4. Strict deterministic Python budget validation
        items, allocations, total_cost, remaining, warnings = budget_engine.validate_budget(
            user_budget=input_data.budget,
            items=clean_items,
            currency=input_data.currency
        )

        print("Response source: GEMINI")
        print("Budget validation: PASSED")
        print("=" * 50)

        # 5. Sourcing platform links
        for it in items:
            it.platform_links = product_link_service.get_links_for_item(
                item_name=it.search_term or it.item_name,
                category=it.category,
                planner_type="home",
                suggested_platforms=it.platforms
            )

        response = PlannerResponseData(
            planner_type="home",
            title=raw_plan.plan_title,
            original_budget=input_data.budget,
            total_estimated_cost=total_cost,
            remaining_budget=remaining,
            currency=input_data.currency,
            summary=raw_plan.summary,
            category_breakdown=allocations,
            items=items,
            warnings=warnings,
            is_fallback=False,
            ai_provider="Google Gemini",
            ai_model=actual_model,
            is_ai_generated=True,
            response_source="GEMINI"
        )

        # 6. Persist
        if user and db:
            record = self._save_record(
                db=db,
                user_id=user.id,
                planner_type="home",
                title=response.title,
                budget=input_data.budget,
                currency=input_data.currency,
                input_dict=input_data.model_dump(),
                response_data=response.model_dump()
            )
            response.plan_id = record.id

        return response

    def process_party_plan(
        self,
        input_data: PartyPlannerInput,
        user: Optional[User] = None,
        db: Optional[Session] = None
    ) -> PlannerResponseData:
        # 1. AI generation
        raw_plan, actual_model = gemini_service.generate_party_plan(input_data)

        # 2. Convert recommendations
        raw_items = self._convert_items(raw_plan.recommendations, default_cat="Event Service")

        # 3. Arithmetic verification & over-budget correction loop (Phase 6)
        clean_items, total = budget_engine.calculate_totals(raw_items)
        max_retries = 2
        retries = 0

        while total > input_data.budget and retries < max_retries:
            retries += 1
            excess = round(total - input_data.budget, 2)
            logger.info(f"Party plan exceeded budget by {excess}. Attempting Gemini revision {retries}/{max_retries}...")
            raw_plan, actual_model = gemini_service.revise_plan_for_budget(
                original_budget=input_data.budget,
                currency=input_data.currency,
                generated_plan=raw_plan,
                calculated_total=total,
                excess_amount=excess,
                planner_name="PARTY"
            )
            raw_items = self._convert_items(raw_plan.recommendations, default_cat="Event Service")
            clean_items, total = budget_engine.calculate_totals(raw_items)

        if total > input_data.budget:
            print("Response source: ERROR")
            print("Budget validation: FAILED")
            print("=" * 50)
            raise GeminiServiceError(
                f"Generated party plan exceeded target budget ({input_data.currency} {input_data.budget:,.2f}) after {retries} revisions."
            )

        # 4. Strict deterministic Python budget validation
        items, allocations, total_cost, remaining, warnings = budget_engine.validate_budget(
            user_budget=input_data.budget,
            items=clean_items,
            currency=input_data.currency
        )

        print("Response source: GEMINI")
        print("Budget validation: PASSED")
        print("=" * 50)

        # 5. Sourcing platform links
        for it in items:
            it.platform_links = product_link_service.get_links_for_item(
                item_name=it.search_term or it.item_name,
                category=it.category,
                planner_type="party",
                suggested_platforms=it.platforms,
                city=input_data.city_location
            )

        response = PlannerResponseData(
            planner_type="party",
            title=raw_plan.plan_title,
            original_budget=input_data.budget,
            total_estimated_cost=total_cost,
            remaining_budget=remaining,
            currency=input_data.currency,
            summary=raw_plan.summary,
            category_breakdown=allocations,
            items=items,
            warnings=warnings,
            is_fallback=False,
            ai_provider="Google Gemini",
            ai_model=actual_model,
            is_ai_generated=True,
            response_source="GEMINI"
        )

        # 6. Persist
        if user and db:
            record = self._save_record(
                db=db,
                user_id=user.id,
                planner_type="party",
                title=response.title,
                budget=input_data.budget,
                currency=input_data.currency,
                input_dict=input_data.model_dump(),
                response_data=response.model_dump()
            )
            response.plan_id = record.id

        return response

    def process_jewelry_plan(
        self,
        input_data: JewelryPlannerInput,
        image_path: Optional[Path] = None,
        image_url: Optional[str] = None,
        user: Optional[User] = None,
        db: Optional[Session] = None
    ) -> PlannerResponseData:
        # 1. AI generation
        raw_plan, actual_model = gemini_service.generate_jewelry_plan(input_data, image_path=image_path)

        # 2. Convert items
        raw_items = self._convert_items(raw_plan.recommendations, default_cat="Jewelry")

        # 3. Arithmetic verification & over-budget correction loop
        clean_items, total = budget_engine.calculate_totals(raw_items)
        max_retries = 2
        retries = 0

        while total > input_data.budget and retries < max_retries:
            retries += 1
            excess = round(total - input_data.budget, 2)
            logger.info(f"Jewelry plan exceeded budget by {excess}. Attempting Gemini revision {retries}/{max_retries}...")
            raw_plan, actual_model = gemini_service.revise_jewelry_plan_for_budget(
                original_budget=input_data.budget,
                currency=input_data.currency,
                generated_plan=raw_plan,
                calculated_total=total,
                excess_amount=excess,
                image_path=image_path
            )
            raw_items = self._convert_items(raw_plan.recommendations, default_cat="Jewelry")
            clean_items, total = budget_engine.calculate_totals(raw_items)

        if total > input_data.budget:
            print("Response source: ERROR")
            print("Budget validation: FAILED")
            print("=" * 50)
            raise GeminiServiceError(
                f"Generated jewelry plan exceeded target budget ({input_data.currency} {input_data.budget:,.2f}) after {retries} revisions."
            )

        # 4. Strict deterministic Python budget validation
        items, allocations, total_cost, remaining, warnings = budget_engine.validate_budget(
            user_budget=input_data.budget,
            items=clean_items,
            currency=input_data.currency
        )

        print("Response source: GEMINI")
        print("Budget validation: PASSED")
        print("=" * 50)

        # 5. Attach platform links
        for it in items:
            it.platform_links = product_link_service.get_links_for_item(
                item_name=it.search_term or it.item_name,
                category=it.category,
                planner_type="jewelry",
                suggested_platforms=it.platforms
            )

        response = PlannerResponseData(
            planner_type="jewelry",
            title=raw_plan.plan_title,
            original_budget=input_data.budget,
            total_estimated_cost=total_cost,
            remaining_budget=remaining,
            currency=input_data.currency,
            summary=raw_plan.summary,
            category_breakdown=allocations,
            items=items,
            outfit_analysis=raw_plan.outfit_analysis,
            outfit_image_url=image_url,
            warnings=warnings,
            is_fallback=False,
            ai_provider="Google Gemini",
            ai_model=actual_model,
            is_ai_generated=True,
            response_source="GEMINI"
        )

        # 6. Persist
        if user and db:
            record = self._save_record(
                db=db,
                user_id=user.id,
                planner_type="jewelry",
                title=response.title,
                budget=input_data.budget,
                currency=input_data.currency,
                input_dict=input_data.model_dump(),
                response_data=response.model_dump(),
                outfit_image_path=image_url
            )
            response.plan_id = record.id

        return response

    def _convert_items(self, gemini_recs: list, default_cat: str) -> List[RecommendationItem]:
        """Converts Gemini recommendation items to internal RecommendationItem schema"""
        items = []
        for r in gemini_recs:
            try:
                platforms = r.suggested_platforms if r.suggested_platforms else ["Amazon", "Flipkart"]
                items.append(
                    RecommendationItem(
                        item_name=r.name,
                        category=r.category or default_cat,
                        description=r.description or "",
                        estimated_price=max(0.0, float(r.estimated_price)),
                        quantity=max(1, int(r.quantity)),
                        reason=r.reason or "Curated by AI for your requirements.",
                        search_term=r.search_terms or r.name,
                        platforms=platforms
                    )
                )
            except Exception as e:
                logger.warning(f"Error parsing Gemini recommendation item: {e}")
        return items

    def _save_record(
        self,
        db: Session,
        user_id: int,
        planner_type: str,
        title: str,
        budget: float,
        currency: str,
        input_dict: dict,
        response_data: dict,
        outfit_image_path: Optional[str] = None
    ) -> RecommendationRecord:
        record = RecommendationRecord(
            user_id=user_id,
            planner_type=planner_type,
            title=title,
            user_budget=budget,
            currency=currency,
            input_data=json.dumps(input_dict),
            result_summary=json.dumps(response_data),
            total_estimated_cost=response_data.get("total_estimated_cost", 0.0),
            remaining_budget=response_data.get("remaining_budget", 0.0),
            outfit_image_path=outfit_image_path
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record


recommendation_service = RecommendationService()
