import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print(f"  Starting {settings.APP_NAME}...")
    print(f"  URL: http://{settings.HOST}:{settings.PORT}")
    print(f"  Gemini Model: {settings.GEMINI_MODEL}")
    print(f"  API Key Configured: {'Yes' if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != 'your_gemini_api_key_here' else 'No (Operating in Smart Fallback Mode)'}")
    print("=" * 60)
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
