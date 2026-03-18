import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    APP_NAME: str = "Hazeon AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./hazeon.db"

    # JWT
    SECRET_KEY: str = "hazeon-super-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Storage
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

    # AI API Keys
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Legacy (kept for backward compat, not hardcoded)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # Fine-tuned model (trained on UPSC topper answers)
    FINETUNED_MODEL_PATH: str = ""      # e.g. ./models/hazeon-upsc-evaluator
    USE_FINETUNED_MODEL: bool = False   # set True after training is done

    # Demo mode — uses mock services when True
    DEMO_MODE: bool = False

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # SMTP / Email (for forgot-password OTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""  # Gmail: use App Password (not account password)
    SMTP_FROM_NAME: str = "Hazeon AI"



settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
