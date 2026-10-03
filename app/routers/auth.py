from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Request, Response, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.schemas import UserRegister, UserLogin, Token, UserOut, SessionInfo
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_optional,
    get_current_user
)
from app.utils.validators import validate_email_str, validate_password_strength

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")


# ==========================================
# HTML Pages
# ==========================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    msg: Optional[str] = None,
    err: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "user": None, "success_message": msg, "error_message": err}
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    err: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "user": None, "error_message": err}
    )


# ==========================================
# Form & API Handlers
# ==========================================

@router.post("/register")
async def register_user(
    request: Request,
    response: Response,
    full_name: str = Form(...),
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Validation
    email_clean = email.strip().lower()
    username_clean = username.strip().lower()

    if not validate_email_str(email_clean):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error_message": "Please enter a valid email address.", "full_name": full_name, "email": email, "username": username},
            status_code=400
        )

    is_valid_pw, pw_err = validate_password_strength(password)
    if not is_valid_pw:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error_message": pw_err, "full_name": full_name, "email": email, "username": username},
            status_code=400
        )

    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error_message": "Passwords do not match.", "full_name": full_name, "email": email, "username": username},
            status_code=400
        )

    # 2. Check duplicates
    if db.query(User).filter(User.email == email_clean).first():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error_message": "An account with this email already exists.", "full_name": full_name, "username": username},
            status_code=400
        )

    if db.query(User).filter(User.username == username_clean).first():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error_message": "This username is already taken. Please choose another.", "full_name": full_name, "email": email},
            status_code=400
        )

    # 3. Create user
    new_user = User(
        full_name=full_name.strip(),
        email=email_clean,
        username=username_clean,
        hashed_password=hash_password(password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. Generate token and set cookie
    access_token = create_access_token(data={"sub": str(new_user.id), "username": new_user.username})
    redirect_res = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    redirect_res.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return redirect_res


@router.post("/login")
async def login_user(
    request: Request,
    response: Response,
    login: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    login_clean = login.strip().lower()
    user = db.query(User).filter(
        (User.email == login_clean) | (User.username == login_clean)
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error_message": "Invalid email/username or password.", "login": login},
            status_code=401
        )

    if not user.is_active:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error_message": "This account is inactive. Please contact support."},
            status_code=403
        )

    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    redirect_res = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    redirect_res.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return redirect_res


@router.get("/logout")
@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/login?msg=You+have+been+logged+out+successfully.", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response


# ==========================================
# REST API Endpoints (as per DOCX spec)
# ==========================================

@router.post("/token", response_model=Token)
async def api_token(login_data: UserLogin, db: Session = Depends(get_db)):
    clean_login = login_data.login.strip().lower()
    user = db.query(User).filter(
        (User.email == clean_login) | (User.username == clean_login)
    ).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )


@router.get("/session-info", response_model=SessionInfo)
async def session_info(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Returns metadata about the current session"""
    if current_user:
        return SessionInfo(authenticated=True, user=UserOut.model_validate(current_user))
    return SessionInfo(authenticated=False, user=None)


@router.get("/session-data")
async def session_data(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Returns detailed session data for recommendation personalization"""
    if not current_user:
        return {"authenticated": False, "message": "Guest session"}
    return {
        "authenticated": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat()
    }
