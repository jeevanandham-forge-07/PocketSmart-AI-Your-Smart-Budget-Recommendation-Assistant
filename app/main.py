import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings, BASE_DIR
from app.database import init_db
from app.models.user import User
from app.utils.security import get_current_user_optional

# Routers
from app.routers import (
    auth,
    dashboard,
    home_planner,
    party_planner,
    jewelry_planner,
    history
)

# Setup logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pocketsmart")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database
    logger.info("Initializing SQLite database tables...")
    init_db()
    # Ensure static upload dir exists
    (BASE_DIR / "static" / "uploads").mkdir(parents=True, exist_ok=True)
    logger.info("PocketSmart AI backend started successfully.")
    yield
    logger.info("Shutting down PocketSmart AI backend...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Your GenAI Smart Budget & Recommendation Assistant for Home, Party, and Jewelry Planning.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
(static_dir / "css").mkdir(exist_ok=True)
(static_dir / "js").mkdir(exist_ok=True)
(static_dir / "images").mkdir(exist_ok=True)
(static_dir / "uploads").mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates_dir = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# Include Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(home_planner.router)
app.include_router(party_planner.router)
app.include_router(jewelry_planner.router)
app.include_router(history.router)


# ==========================================
# Landing Page & Public Pages
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def landing_page(
    request: Request,
    current_user: User = Depends(get_current_user_optional)
):
    """Main Landing Page"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user": current_user}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "model": settings.GEMINI_MODEL,
        "environment": settings.APP_ENV
    }


# ==========================================
# Exception Handlers (Clean UI without traces)
# ==========================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if "application/json" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "status_code": exc.status_code, "error_detail": exc.detail},
            status_code=exc.status_code
        )
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": exc.status_code, "error_detail": exc.detail},
        status_code=exc.status_code
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 500,
            "error_detail": "An unexpected error occurred while processing your request. Please try again."
        },
        status_code=500
    )
