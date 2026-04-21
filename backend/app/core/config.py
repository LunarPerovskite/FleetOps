from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    APP_NAME: str = "FleetOps"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://fleetops:fleetops@localhost/fleetops"
    DATABASE_URL_SYNC: str = "postgresql://fleetops:fleetops@localhost/fleetops"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Auth
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Agent connectors
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Evidence store
    EVIDENCE_HOT_DAYS: int = 90
    EVIDENCE_COLD_DAYS: int = 365
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
