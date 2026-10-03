from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.recommendation import RecommendationRecord
from app.models.schemas import PlannerResponseData
from app.utils.security import get_current_user_optional

router = APIRouter(tags=["History"])
templates = Jinja2Templates(directory="templates")


@router.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(
            url="/login?err=Please+log+in+to+view+your+saved+recommendation+history.",
            status_code=status.HTTP_302_FOUND
        )

    records = db.query(RecommendationRecord).filter(
        RecommendationRecord.user_id == current_user.id
    ).order_by(RecommendationRecord.created_at.desc()).all()

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "user": current_user,
            "records": records
        }
    )


@router.get("/history/{record_id}", response_class=HTMLResponse)
async def view_history_item(
    record_id: int,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    record = db.query(RecommendationRecord).filter(
        RecommendationRecord.id == record_id,
        RecommendationRecord.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Saved recommendation not found.")

    plan_dict = record.parsed_result
    input_dict = record.parsed_input

    # Reconstruct PlannerResponseData
    try:
        plan_obj = PlannerResponseData.model_validate(plan_dict)
    except Exception:
        # Fallback if raw dict format
        plan_obj = plan_dict

    planner_display_names = {
        "home": "Home Interior Budget Plan",
        "party": "Party & Event Budget Plan",
        "jewelry": "Jewelry & Outfit Styling Plan"
    }

    return templates.TemplateResponse(
        "recommendation_result.html",
        {
            "request": request,
            "user": current_user,
            "plan": plan_obj,
            "input_data": input_dict,
            "planner_name": planner_display_names.get(record.planner_type, "Saved Budget Plan"),
            "saved_record": record
        }
    )


@router.post("/history/{record_id}/delete")
async def delete_history_item(
    record_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    record = db.query(RecommendationRecord).filter(
        RecommendationRecord.id == record_id,
        RecommendationRecord.user_id == current_user.id
    ).first()

    if record:
        db.delete(record)
        db.commit()

    return RedirectResponse(url="/history", status_code=status.HTTP_302_FOUND)
