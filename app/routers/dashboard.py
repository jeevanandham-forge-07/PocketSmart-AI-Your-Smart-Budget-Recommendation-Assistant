from typing import Optional
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.recommendation import RecommendationRecord
from app.utils.security import get_current_user_optional

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login?err=Please+sign+in+to+access+your+dashboard.", status_code=status.HTTP_302_FOUND)

    # Fetch user's recent recommendations
    recent_plans = db.query(RecommendationRecord).filter(
        RecommendationRecord.user_id == current_user.id
    ).order_by(RecommendationRecord.created_at.desc()).limit(6).all()

    total_plans = db.query(RecommendationRecord).filter(
        RecommendationRecord.user_id == current_user.id
    ).count()

    total_budget_planned = sum(p.user_budget for p in db.query(RecommendationRecord.user_budget).filter(
        RecommendationRecord.user_id == current_user.id
    ).all())

    total_budget_saved = sum(p.remaining_budget for p in db.query(RecommendationRecord.remaining_budget).filter(
        RecommendationRecord.user_id == current_user.id
    ).all())

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
            "recent_plans": recent_plans,
            "total_plans": total_plans,
            "total_budget_planned": total_budget_planned,
            "total_budget_saved": total_budget_saved
        }
    )
