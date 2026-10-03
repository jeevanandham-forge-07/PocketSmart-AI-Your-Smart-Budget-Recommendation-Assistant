from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


# ==========================================
# Authentication & User Schemas
# ==========================================

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=6, max_length=100)

    @field_validator("confirm_password")
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("username")
    def username_alphanumeric(cls, v):
        clean = v.replace("_", "").replace("-", "")
        if not clean.isalnum():
            raise ValueError("Username must contain only letters, numbers, hyphens, and underscores")
        return v.strip().lower()


class UserLogin(BaseModel):
    login: str = Field(..., description="Email or Username")
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: str
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SessionInfo(BaseModel):
    authenticated: bool
    user: Optional[UserOut] = None


# ==========================================
# Planner Input Schemas
# ==========================================

class HomePlannerInput(BaseModel):
    budget: float = Field(..., gt=0, description="Total budget in INR or specified currency")
    currency: str = Field("INR", max_length=10)
    living_room: bool = True
    bedroom_count: int = Field(1, ge=0, le=20)
    kitchen: bool = True
    dining_room: bool = True
    lights_count: int = Field(6, ge=0, le=200)
    fans_count: int = Field(2, ge=0, le=50)
    dining_table_count: int = Field(1, ge=0, le=10)
    furniture_requirements: Optional[str] = Field("", max_length=500)
    decor_requirements: Optional[str] = Field("", max_length=500)
    preferred_style: str = Field("Modern", max_length=100)
    color_preferences: Optional[str] = Field("Warm Neutral", max_length=200)
    additional_requirements: Optional[str] = Field("", max_length=1000)

    @field_validator("budget")
    def validate_budget(cls, v):
        if v <= 0:
            raise ValueError("Budget must be greater than 0")
        if v > 100_000_000:
            raise ValueError("Budget exceeds maximum allowable limit")
        return round(float(v), 2)


class PartyPlannerInput(BaseModel):
    budget: float = Field(..., gt=0, description="Total party budget")
    currency: str = Field("INR", max_length=10)
    guest_count: int = Field(..., gt=0, le=5000, description="Estimated number of guests")
    event_type: str = Field("Birthday", max_length=100)
    city_location: str = Field("Chennai", max_length=100)
    venue_required: bool = True
    catering_required: bool = True
    decoration_required: bool = True
    entertainment_required: bool = False
    cake_required: bool = True
    photography_required: bool = False
    transport_required: bool = False
    accommodation_required: bool = False
    food_preference: str = Field("Multi-Cuisine", max_length=100)
    event_date: Optional[str] = Field("", max_length=50)
    additional_requirements: Optional[str] = Field("", max_length=1000)

    @field_validator("budget")
    def validate_budget(cls, v):
        if v <= 0:
            raise ValueError("Budget must be greater than 0")
        if v > 100_000_000:
            raise ValueError("Budget exceeds maximum allowable limit")
        return round(float(v), 2)


class JewelryPlannerInput(BaseModel):
    budget: float = Field(..., gt=0, description="Total jewelry budget")
    currency: str = Field("INR", max_length=10)
    occasion: str = Field("Wedding", max_length=100)
    jewelry_type: str = Field("Complete Set", max_length=100)
    style_preference: str = Field("Traditional", max_length=100)
    metal_preference: str = Field("Gold Plated", max_length=100)
    color_preference: Optional[str] = Field("", max_length=100)
    additional_requirements: Optional[str] = Field("", max_length=1000)

    @field_validator("budget")
    def validate_budget(cls, v):
        if v <= 0:
            raise ValueError("Budget must be greater than 0")
        if v > 100_000_000:
            raise ValueError("Budget exceeds maximum allowable limit")
        return round(float(v), 2)


# ==========================================
# Structured Output Schemas
# ==========================================

class RecommendationItem(BaseModel):
    item_name: str
    category: str
    description: str
    estimated_price: float = Field(..., ge=0)
    quantity: int = Field(1, ge=1)
    subtotal: float = Field(0.0, ge=0)
    reason: str
    search_term: str
    platforms: List[str] = Field(default_factory=lambda: ["Amazon", "Flipkart"])
    platform_links: Dict[str, str] = Field(default_factory=dict)

    def calculate_subtotal(self) -> float:
        self.subtotal = round(self.estimated_price * self.quantity, 2)
        return self.subtotal


class CategoryAllocation(BaseModel):
    category: str
    allocated_amount: float = Field(..., ge=0)
    percentage: float = Field(0.0, ge=0, le=100)
    description: Optional[str] = ""


class OutfitAnalysis(BaseModel):
    dominant_colors: List[str] = Field(default_factory=list)
    secondary_colors: List[str] = Field(default_factory=list)
    style_vibe: str = ""
    formality_level: str = ""
    jewelry_coordination_advice: str = ""


class PlannerResponseData(BaseModel):
    plan_id: Optional[int] = None
    planner_type: str  # 'home', 'party', 'jewelry'
    title: str
    original_budget: float
    total_estimated_cost: float
    remaining_budget: float
    currency: str = "INR"
    summary: str
    category_breakdown: List[CategoryAllocation] = Field(default_factory=list)
    items: List[RecommendationItem] = Field(default_factory=list)
    outfit_analysis: Optional[OutfitAnalysis] = None
    outfit_image_url: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    is_fallback: bool = False
    ai_provider: str = "Google Gemini"
    ai_model: Optional[str] = None
    is_ai_generated: bool = True
    response_source: str = "GEMINI"


# ==========================================
# Gemini Structured Output Schemas
# ==========================================

class GeminiRecommendationItem(BaseModel):
    category: str = Field(..., description="Category like Catering, Venue, Furniture, Lighting, etc.")
    name: str = Field(..., description="Specific recommendation or service name")
    description: str = Field(..., description="Concise description of the item or package")
    estimated_price: float = Field(..., ge=0, description="Estimated unit cost in local currency")
    quantity: int = Field(1, ge=1, description="Quantity or headcount needed")
    reason: str = Field(..., description="Why this item matches the user's requirements and style")
    search_terms: str = Field(..., description="Specific keyword query for finding this item online")
    suggested_platforms: List[str] = Field(
        default_factory=lambda: ["Amazon", "Flipkart"],
        description="Suggested e-commerce / booking platforms like Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, CaratLane, Myntra"
    )


class GeminiPlanOutput(BaseModel):
    plan_title: str = Field(..., description="Attractive descriptive title for the plan")
    summary: str = Field(..., description="Strategic summary explaining the budget allocation approach")
    budget: float = Field(..., description="Target budget provided by the user")
    recommendations: List[GeminiRecommendationItem] = Field(
        ...,
        description="List of recommended items whose sum of (estimated_price * quantity) does not exceed budget"
    )
    additional_tips: List[str] = Field(default_factory=list, description="Practical savings or execution tips")


class GeminiJewelryPlanOutput(BaseModel):
    plan_title: str = Field(..., description="Attractive descriptive title for the jewelry styling plan")
    summary: str = Field(..., description="Strategic summary of jewelry ensemble and styling coordination")
    budget: float = Field(..., description="Target jewelry budget")
    recommendations: List[GeminiRecommendationItem] = Field(
        ...,
        description="List of recommended jewelry items whose sum does not exceed budget"
    )
    outfit_analysis: Optional[OutfitAnalysis] = Field(
        None,
        description="Detailed outfit visual analysis when outfit image or description is supplied"
    )
    additional_tips: List[str] = Field(default_factory=list, description="Styling tips and accessorizing advice")

