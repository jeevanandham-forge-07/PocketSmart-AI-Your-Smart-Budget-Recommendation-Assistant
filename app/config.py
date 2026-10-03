import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)



class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "PocketSmart AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # AI Configuration
    GEMINI_API_KEY: str = "AQ.Ab8RN6JR6CbMwj13m9Lu-IqT0gjQ-nekSYA7xgkBsbPrHkQokw"
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"

    # Security & Auth
    SECRET_KEY: str = "pocketsmart_secret_key_default_development_token_98124"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'pocketsmart.db'}"

    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 5
    UPLOAD_DIR: Path = BASE_DIR / "static" / "uploads"
    ALLOWED_IMAGE_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png", ".webp"]


settings = Settings()

# Ensure uploads directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
