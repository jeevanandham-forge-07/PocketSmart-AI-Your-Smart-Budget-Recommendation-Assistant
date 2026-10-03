from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.schemas import JewelryPlannerInput, PlannerResponseData
from app.services.image_service import image_service
from app.services.recommendation_service import recommendation_service
from app.services.gemini_service import GeminiServiceError
from app.utils.security import get_current_user_optional

router = APIRouter(tags=["Jewelry Planner"])
templates = Jinja2Templates(directory="templates")


@router.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    return templates.TemplateResponse(
        "jewelry_planner.html",
        {"request": request, "user": current_user}
    )


@router.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    budget: float = Form(...),
    currency: str = Form("INR"),
    occasion: str = Form("Wedding"),
    jewelry_type: str = Form("Complete Set"),
    style_preference: str = Form("Traditional"),
    metal_preference: str = Form("Gold Plated"),
    color_preference: Optional[str] = Form(""),
    additional_requirements: Optional[str] = Form(""),
    outfit_image: Optional[UploadFile] = File(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    try:
        input_data = JewelryPlannerInput(
            budget=budget,
            currency=currency,
            occasion=occasion,
            jewelry_type=jewelry_type,
            style_preference=style_preference,
            metal_preference=metal_preference,
            color_preference=color_preference,
            additional_requirements=additional_requirements
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "jewelry_planner.html",
            {"request": request, "user": current_user, "error_message": str(e)},
            status_code=400
        )

    # Handle image upload if provided
    image_rel_url = None
    image_path: Optional[Path] = None
    if outfit_image and outfit_image.filename:
        try:
            image_rel_url, image_path = image_service.validate_and_save_upload(outfit_image)
        except HTTPException as he:
            return templates.TemplateResponse(
                "jewelry_planner.html",
                {"request": request, "user": current_user, "error_message": he.detail},
                status_code=400
            )

    try:
        plan_result = recommendation_service.process_jewelry_plan(
            input_data=input_data,
            image_path=image_path,
            image_url=image_rel_url,
            user=current_user,
            db=db
        )
    except GeminiServiceError as ge:
        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse(status_code=503, content={"detail": str(ge)})
        return templates.TemplateResponse(
            "jewelry_planner.html",
            {"request": request, "user": current_user, "error_message": str(ge)},
            status_code=503
        )
    except Exception as e:
        if "application/json" in request.headers.get("accept", ""):
            return JSONResponse(status_code=500, content={"detail": "AI recommendation unavailable. Please try again."})
        return templates.TemplateResponse(
            "jewelry_planner.html",
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
            "planner_name": "Jewelry & Outfit Styling Plan"
        }
    )


@router.post("/api/generate-jewelry", response_model=PlannerResponseData)
async def api_generate_jewelry(
    input_data: JewelryPlannerInput,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """JSON API endpoint for Jewelry Planner (text only)"""
    try:
        return recommendation_service.process_jewelry_plan(
            input_data=input_data,
            user=current_user,
            db=db
        )
    except GeminiServiceError as ge:
        raise HTTPException(status_code=503, detail=str(ge))
    except Exception as e:
        raise HTTPException(status_code=500, detail="AI recommendation unavailable. Please try again.")
