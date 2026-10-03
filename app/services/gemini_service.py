import json
import logging
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Type
from dotenv import load_dotenv
from PIL import Image

from app.config import settings, BASE_DIR
from app.models.schemas import (
    HomePlannerInput,
    PartyPlannerInput,
    JewelryPlannerInput,
    GeminiPlanOutput,
    GeminiJewelryPlanOutput,
    GeminiRecommendationItem,
    OutfitAnalysis
)

load_dotenv(dotenv_path=BASE_DIR / ".env")
logger = logging.getLogger("pocketsmart.gemini")


class GeminiServiceError(Exception):
    """Raised when Gemini API generation fails or budget limits cannot be met"""
    pass


class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        self.model_name = os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL
        self._genai_client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initializes the official Google GenAI client safely"""
        self.api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        self.model_name = os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL
        if not self.api_key or self.api_key.strip() in ("", "your_gemini_api_key_here"):
            logger.warning("No valid GEMINI_API_KEY configured.")
            return

        try:
            from google import genai
            self._genai_client = genai.Client(api_key=self.api_key)
            logger.info("Google GenAI client successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize google.genai client: {e}")
            self._genai_client = None

    @property
    def is_available(self) -> bool:
        key = os.getenv("GEMINI_API_KEY") or self.api_key
        return self._genai_client is not None and bool(key and key != "your_gemini_api_key_here")

    def _get_candidate_models(self) -> List[str]:
        """Returns prioritized list of live Gemini models to handle transient outages gracefully"""
        configured = os.getenv("GEMINI_MODEL") or self.model_name or "gemini-2.5-flash-lite"
        candidates = [configured, "gemini-2.5-flash-lite", "gemini-flash-lite-latest", "gemini-3-flash-preview"]
        seen = set()
        deduped = []
        for c in candidates:
            if c and c not in seen:
                seen.add(c)
                deduped.append(c)
        return deduped

    def _call_structured_model(
        self,
        prompt: str,
        response_schema: Type[Any],
        image_path: Optional[Path] = None,
        planner_name: str = "PLANNER"
    ) -> Tuple[Any, str]:
        """
        Executes Gemini request with structured Pydantic JSON schema and development trace logging.
        Never exposes the API key.
        """
        if not self.is_available:
            self._log_terminal_failure(planner_name, self.model_name or "gemini", "Gemini API client not initialized or missing API key.")
            raise GeminiServiceError("AI recommendation unavailable. Please configure GEMINI_API_KEY.")

        candidate_models = self._get_candidate_models()
        last_exception = None

        print("=" * 50)
        print("POCKETSMART AI REQUEST")
        print(f"Planner: {planner_name.upper()}")
        print("AI Provider: Google Gemini")
        print(f"Model: {candidate_models[0]}")
        print("Gemini API call: STARTED")

        from google.genai import types

        for model_to_try in candidate_models:
            try:
                contents: List[Any] = [prompt]
                is_multimodal = False

                if image_path and image_path.exists():
                    pil_img = Image.open(image_path)
                    contents.append(pil_img)
                    is_multimodal = True

                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema
                )

                response = self._genai_client.models.generate_content(
                    model=model_to_try,
                    contents=contents,
                    config=config
                )

                if is_multimodal:
                    print("Multimodal Gemini call: SUCCESS")

                print("Gemini API call: SUCCESS")

                raw_text = response.text or ""
                # Parse structured output with Pydantic
                parsed_data = response_schema.model_validate_json(raw_text)
                return parsed_data, model_to_try

            except Exception as e:
                last_exception = e
                logger.warning(f"Gemini model '{model_to_try}' request failed: {e}. Checking backup models...")

        print("Gemini API call: FAILED")
        print("Response source: ERROR")
        print("=" * 50)
        logger.error(f"All Gemini models exhausted. Final exception: {last_exception}")
        raise GeminiServiceError("AI recommendation unavailable. Please try again.")

    def _log_terminal_failure(self, planner_name: str, model_name: str, reason: str):
        print("=" * 50)
        print("POCKETSMART AI REQUEST")
        print(f"Planner: {planner_name.upper()}")
        print("AI Provider: Google Gemini")
        print(f"Model: {model_name}")
        print("Gemini API call: FAILED")
        print("Response source: ERROR")
        print(f"Failure reason: {reason}")
        print("=" * 50)

    # ==========================================
    # 1. HOME INTERIOR PLANNER
    # ==========================================
    def generate_home_plan(self, data: HomePlannerInput) -> Tuple[GeminiPlanOutput, str]:
        """Generate dynamic structured home interior recommendations via Gemini"""
        rooms_list = []
        if data.living_room:
            rooms_list.append("Living Room")
        if data.bedroom_count > 0:
            rooms_list.append(f"{data.bedroom_count} Bedroom(s)")
        if data.kitchen:
            rooms_list.append("Kitchen")
        if data.dining_room:
            rooms_list.append("Dining Room")

        prompt = f"""
You are an expert interior designer and smart home budgeting assistant for PocketSmart AI.
Analyze the user's home interior requirements and budget to recommend a balanced list of items (furniture, lighting, fans, decor, storage, dining).

USER REQUIREMENTS:
- Total Target Budget: {data.currency} {data.budget:,.2f}
- Rooms to furnish/decorate: {', '.join(rooms_list) if rooms_list else 'Full House'}
- Number of Lights required: {data.lights_count}
- Number of Fans required: {data.fans_count}
- Dining Table setups: {data.dining_table_count}
- Specific Furniture Needs: {data.furniture_requirements or 'Essential matching furniture'}
- Specific Decor Needs: {data.decor_requirements or 'Tasteful aesthetic decor'}
- Preferred Design Style: {data.preferred_style}
- Color Palette / Preferences: {data.color_preferences or 'Harmonious neutrals'}
- Additional Notes: {data.additional_requirements or 'None'}

CRITICAL RULES:
1. Provide a curated list of recommendations across categories (e.g. Furniture, Lighting, Fans, Dining, Decor, Storage).
2. The sum of (estimated_price * quantity) for all items MUST be strictly within the user's budget ({data.currency} {data.budget:,.2f}).
3. Never use fixed rigid percentage formulas. Dynamically decide item quantities, realistic prices, and selections tailored to the requested rooms and style.
4. For lighting, provide fixtures covering {data.lights_count} lights. For fans, provide {data.fans_count} fans. For dining, provide {data.dining_table_count} setup(s).
5. Suggest realistic Indian e-commerce / decor platforms (e.g., IKEA, Amazon, Flipkart, Pepperfry).
6. Give specific styling reasoning for each item explaining how it complements the {data.preferred_style} style.
"""
        return self._call_structured_model(
            prompt=prompt,
            response_schema=GeminiPlanOutput,
            planner_name="HOME"
        )

    # ==========================================
    # 2. PARTY PLANNER
    # ==========================================
    def generate_party_plan(self, data: PartyPlannerInput) -> Tuple[GeminiPlanOutput, str]:
        """Generate dynamic structured party budget recommendations via Gemini"""
        needed_services = []
        if data.venue_required:
            needed_services.append("Venue / Banquet Space")
        if data.catering_required:
            needed_services.append("Catering / Food & Beverages")
        if data.decoration_required:
            needed_services.append("Theme Decoration & Ambience")
        if data.entertainment_required:
            needed_services.append("DJ / Music & Entertainment")
        if data.cake_required:
            needed_services.append("Celebration Cake")
        if data.photography_required:
            needed_services.append("Photography & Videography")
        if data.transport_required:
            needed_services.append("Guest Transport")
        if data.accommodation_required:
            needed_services.append("Guest Hotel Accommodation")

        prompt = f"""
You are an expert event planner and smart party budgeting assistant for PocketSmart AI.
Analyze the user's event details and total budget to create a realistic, dynamic cost plan with tailored vendor and service packages.

USER REQUIREMENTS:
- Total Target Budget: {data.currency} {data.budget:,.2f}
- Event Type: {data.event_type}
- Guest Count: {data.guest_count} people
- City / Location: {data.city_location}
- Food Preference: {data.food_preference}
- Required Services: {', '.join(needed_services) if needed_services else 'All essentials'}
- Target Event Date: {data.event_date or 'Upcoming'}
- Special Requests: {data.additional_requirements or 'None'}

CRITICAL RULES:
1. ONLY recommend categories requested by the user. For instance:
   - If venue_required is False, DO NOT include a Venue item!
   - If entertainment_required is False, DO NOT include DJ/Entertainment!
   - If cake_required is False, DO NOT include a Cake item!
2. For Catering (if requested):
   - Set 'quantity' to {data.guest_count} (guests)
   - Set 'estimated_price' to the realistic per-guest plate cost in {data.city_location} for {data.food_preference}.
3. The total cost, calculated as sum(estimated_price * quantity), MUST be less than or equal to {data.currency} {data.budget:,.2f}.
4. DO NOT use static pre-calculated percentages (like 45% catering, 25% venue, 12% decor). Decide custom allocations dynamically based on {data.guest_count} guests, {data.event_type}, and the selected services.
5. Assign appropriate platforms (e.g. Swiggy, Zomato for catering/cake, OYO, MakeMyTrip for venue/stay, Amazon, Flipkart for decor/accessories).
"""
        return self._call_structured_model(
            prompt=prompt,
            response_schema=GeminiPlanOutput,
            planner_name="PARTY"
        )

    # ==========================================
    # 3. JEWELRY PLANNER (Multimodal)
    # ==========================================
    def generate_jewelry_plan(
        self,
        data: JewelryPlannerInput,
        image_path: Optional[Path] = None
    ) -> Tuple[GeminiJewelryPlanOutput, str]:
        """Generate dynamic jewelry styling recommendations with multimodal outfit analysis"""
        image_instruction = ""
        if image_path and image_path.exists():
            image_instruction = """
ANALYZE THE ATTACHED OUTFIT IMAGE IN DETAIL:
1. Identify dominant colors and secondary color accents of the outfit garment.
2. Discern the style vibe (e.g. Traditional Royal, Minimalist Contemporary, Indo-Western Fusion, Classic Silk).
3. Determine formality level (Casual, Festive, Formal, Bridal / Grand).
4. Provide comprehensive jewelry coordination advice explaining which metal tones, stone colors, and silhouettes flatter the neckline and silhouette.
5. Populate the 'outfit_analysis' section in the JSON response accordingly.
"""
        else:
            image_instruction = """
No outfit image was provided. Based on the user's occasion, style preference, and color preference:
1. Provide thoughtful styling coordination advice in 'outfit_analysis.jewelry_coordination_advice'.
2. List complementary color accents in dominant/secondary colors.
"""

        prompt = f"""
You are a premier celebrity jewelry stylist and smart budget advisor for PocketSmart AI.
Analyze the user's styling requirements and budget to curate a coordinated jewelry ensemble.

USER REQUIREMENTS:
- Total Target Budget: {data.currency} {data.budget:,.2f}
- Occasion: {data.occasion}
- Jewelry Type Preferred: {data.jewelry_type}
- Style Preference: {data.style_preference}
- Metal Preference: {data.metal_preference}
- Outfit Color Palette: {data.color_preference or 'Not specified'}
- Additional Styling Notes: {data.additional_requirements or 'None'}

{image_instruction}

CRITICAL RULES:
1. Recommend pieces completing the look (e.g. Necklace, Earrings, Bangles/Bracelets, Maang Tikka, Rings).
2. The total sum of (estimated_price * quantity) for all recommended jewelry items MUST NOT exceed {data.currency} {data.budget:,.2f}.
3. Provide realistic estimated prices based on {data.metal_preference} (e.g. Gold Plated, Kundan, Sterling Silver, Fashion Jewelry).
4. Assign suitable shopping platforms (e.g., CaratLane, Myntra, Amazon, Flipkart).
5. Give detailed styling rationale for why each jewelry piece pairs with the {data.occasion} and {data.style_preference} aesthetic.
"""
        return self._call_structured_model(
            prompt=prompt,
            response_schema=GeminiJewelryPlanOutput,
            image_path=image_path,
            planner_name="JEWELRY"
        )

    # ==========================================
    # 4. OVER-BUDGET CORRECTION REVISION (Phase 6)
    # ==========================================
    def revise_plan_for_budget(
        self,
        original_budget: float,
        currency: str,
        generated_plan: GeminiPlanOutput,
        calculated_total: float,
        excess_amount: float,
        planner_name: str
    ) -> Tuple[GeminiPlanOutput, str]:
        """
        Sends correction request back to Gemini when an initial plan exceeds budget.
        Gemini dynamically adjusts items to strictly satisfy budget constraints.
        """
        prompt = f"""
BUDGET REVISION REQUEST:
The previously generated {planner_name} plan has a calculated total of {currency} {calculated_total:,.2f}, which exceeds the user's strict maximum budget of {currency} {original_budget:,.2f} by {currency} {excess_amount:,.2f}.

PREVIOUS PLAN:
{generated_plan.model_dump_json(indent=2)}

INSTRUCTIONS:
1. Revise the recommendations so that the SUM of (estimated_price * quantity) is strictly LESS THAN OR EQUAL TO {currency} {original_budget:,.2f}.
2. Preserve the user's primary requirements, style, and essential services by adjusting estimated prices to more affordable vendor tiers or moderating non-essential specifications.
3. DO NOT scale numbers using a blind percentage; intelligently re-allocate costs across items.
4. Return the revised plan matching the exact schema.
"""
        return self._call_structured_model(
            prompt=prompt,
            response_schema=GeminiPlanOutput,
            planner_name=f"{planner_name}-REVISION"
        )

    def revise_jewelry_plan_for_budget(
        self,
        original_budget: float,
        currency: str,
        generated_plan: GeminiJewelryPlanOutput,
        calculated_total: float,
        excess_amount: float,
        image_path: Optional[Path] = None
    ) -> Tuple[GeminiJewelryPlanOutput, str]:
        """Revision for Jewelry Plan over-budget"""
        prompt = f"""
BUDGET REVISION REQUEST (JEWELRY):
The previous jewelry plan totaled {currency} {calculated_total:,.2f}, exceeding the maximum budget of {currency} {original_budget:,.2f} by {currency} {excess_amount:,.2f}.

PREVIOUS PLAN:
{generated_plan.model_dump_json(indent=2)}

INSTRUCTIONS:
1. Re-balance the jewelry recommendations so the sum of (estimated_price * quantity) is strictly <= {currency} {original_budget:,.2f}.
2. Select more cost-effective designs, plated metals, or semi-precious stone alternatives that preserve the overall look.
3. Keep the outfit analysis intact.
"""
        return self._call_structured_model(
            prompt=prompt,
            response_schema=GeminiJewelryPlanOutput,
            image_path=image_path,
            planner_name="JEWELRY-REVISION"
        )


gemini_service = GeminiService()
