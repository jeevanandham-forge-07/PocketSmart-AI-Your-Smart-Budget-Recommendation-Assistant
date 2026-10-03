from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.schemas import PartyPlannerInput, PlannerResponseData
from app.services.recommendation_service import recommendation_service
from app.services.gemini_service import GeminiServiceError
from app.utils.security import get_current_user_optional

router = APIRouter(tags=["Party Planner"])
templates = Jinja2Templates(directory="templates")


@router.get("/party-planner", response_class=HTMLResponse)
async def party_planner_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    return templates.TemplateResponse(
        "party_planner.html",
        {"request": request, "user": current_user}
    )


@router.post("/generate-party")
async def generate_party(
    request: Request,
    budget: float = Form(...),
    currency: str = Form("INR"),
    guest_count: int = Form(...),
    event_type: str = Form("Birthday"),
    city_location: str = Form("Chennai"),
    venue_required: Optional[bool] = Form(False),
    catering_required: Optional[bool] = Form(False),
    decoration_required: Optional[bool] = Form(False),
    entertainment_required: Optional[bool] = Form(False),
    cake_required: Optional[bool] = Form(False),
    photography_required: Optional[bool] = Form(False),
    transport_required: Optional[bool] = Form(False),
    accommodation_required: Optional[bool] = Form(False),
    food_preference: str = Form("Multi-Cuisine"),
    event_date: Optional[str] = Form(""),
    additional_requirements: Optional[str] = Form(""),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    try:
        input_data = PartyPlannerInput(
            budget=budget,
            currency=currency,
            guest_count=guest_count,
            event_type=event_type,
            city_location=city_location,
            venue_required=bool(venue_required),
            catering_required=bool(catering_required),
            decoration_required=bool(decoration_required),
            entertainment_required=bool(entertainment_required),
            cake_required=bool(cake_required),
            photography_required=bool(photography_required),
            transport_required=bool(transport_required),
            accommodation_required=bool(accommodation_required),
            food_preference=food_preference,
            event_date=event_date,
            additional_requirements=additional_requirements
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "party_planner.html",
            {"request": request, "user": current_user, "error_message": str(e)},
            status_code=400
        )

    try:
        plan_result = recommendation_service.process_party_plan(
            input_data=input_data,
            user=current_user,
            db=db
        )
    except GeminiServiceError as ge:
        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse(status_code=503, content={"detail": str(ge)})
        return templates.TemplateResponse(
            "party_planner.html",
            {"request": request, "user": current_user, "error_message": str(ge)},
            status_code=503
        )
    except Exception as e:
        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse(status_code=500, content={"detail": "AI recommendation unavailable. Please try again."})
        return templates.TemplateResponse(
            "party_planner.html",
            {"request": request, "user": current_user, "error_message": "AI recommendation unavailable. Please try again."},
            status_code=500
        )

    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(content=plan_result.model_dump())

    return templates.TemplateResponse(
        "recommendation_result.html",
        {
            "request": request,
            "user": current_user,
            "plan": plan_result,
            "input_data": input_data.model_dump(),
            "planner_name": "Party & Event Budget Plan"
        }
    )


@router.post("/api/generate-party", response_model=PlannerResponseData)
async def api_generate_party(
    input_data: PartyPlannerInput,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """JSON API endpoint for Party Planner"""
    try:
        return recommendation_service.process_party_plan(
            input_data=input_data,
            user=current_user,
            db=db
        )
    except GeminiServiceError as ge:
        raise HTTPException(status_code=503, detail=str(ge))
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI recommendation unavailable. Please try again.")
