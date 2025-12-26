from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # GCP Config (Unified)
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(..., description="Path to the Google Service Account JSON")
    GCP_PROJECT_ID: str = Field(..., description="Google Cloud Project ID")
    GCP_LOCATION: str = Field(..., description="Google Cloud Region (RAG)")
    GCP_LOCATION_CHAT: str = Field(..., description="Google Cloud Region (Chat/Gemini)")

    # API Config
    API_TITLE: str = "RAG Facade API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    PORT: int = 8000

    # JWT Configuration
    JWT_SECRET_KEY: str = Field(..., description="Secret key for JWT signing")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=720, description="Token expiration in hours (default: 30 days)")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
