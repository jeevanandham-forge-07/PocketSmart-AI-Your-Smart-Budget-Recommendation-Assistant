from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.schemas import HomePlannerInput, PlannerResponseData
from app.services.recommendation_service import recommendation_service
from app.services.gemini_service import GeminiServiceError
from app.utils.security import get_current_user_optional

router = APIRouter(tags=["Home Interior Planner"])
templates = Jinja2Templates(directory="templates")


@router.get("/home-planner", response_class=HTMLResponse)
async def home_planner_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    return templates.TemplateResponse(
        "home_planner.html",
        {"request": request, "user": current_user}
    )


@router.post("/generate-home")
async def generate_home(
    request: Request,
    budget: float = Form(...),
    currency: str = Form("INR"),
    living_room: Optional[bool] = Form(False),
    bedroom_count: int = Form(1),
    kitchen: Optional[bool] = Form(False),
    dining_room: Optional[bool] = Form(False),
    lights_count: int = Form(6),
    fans_count: int = Form(2),
    dining_table_count: int = Form(1),
    furniture_requirements: Optional[str] = Form(""),
    decor_requirements: Optional[str] = Form(""),
    preferred_style: str = Form("Modern"),
    color_preferences: Optional[str] = Form("Neutral"),
    additional_requirements: Optional[str] = Form(""),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    try:
        input_data = HomePlannerInput(
            budget=budget,
            currency=currency,
            living_room=bool(living_room),
            bedroom_count=bedroom_count,
            kitchen=bool(kitchen),
            dining_room=bool(dining_room),
            lights_count=lights_count,
            fans_count=fans_count,
            dining_table_count=dining_table_count,
            furniture_requirements=furniture_requirements,
            decor_requirements=decor_requirements,
            preferred_style=preferred_style,
            color_preferences=color_preferences,
            additional_requirements=additional_requirements
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "home_planner.html",
            {"request": request, "user": current_user, "error_message": str(e)},
            status_code=400
        )

    try:
        plan_result = recommendation_service.process_home_plan(
            input_data=input_data,
            user=current_user,
            db=db
        )
    except GeminiServiceError as ge:
        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse(status_code=503, content={"detail": str(ge)})
        return templates.TemplateResponse(
            "home_planner.html",
            {"request": request, "user": current_user, "error_message": str(ge)},
            status_code=503
        )
    except Exception as e:
        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse(status_code=500, content={"detail": "AI recommendation unavailable. Please try again."})
        return templates.TemplateResponse(
            "home_planner.html",
            {"request": request, "user": current_user, "error_message": "AI recommendation unavailable. Please try again."},
            status_code=500
        )

    # Check if client asked for JSON (API call)
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(content=plan_result.model_dump())

    return templates.TemplateResponse(
        "recommendation_result.html",
        {
            "request": request,
            "user": current_user,
            "plan": plan_result,
            "input_data": input_data.model_dump(),
            "planner_name": "Home Interior Budget Plan"
        }
    )


@router.post("/api/generate-home", response_model=PlannerResponseData)
async def api_generate_home(
    input_data: HomePlannerInput,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """JSON API endpoint for Home Planner"""
    try:
        return recommendation_service.process_home_plan(
            input_data=input_data,
            user=current_user,
            db=db
        )
    except GeminiServiceError as ge:
        raise HTTPException(status_code=503, detail=str(ge))
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI recommendation unavailable. Please try again.")
