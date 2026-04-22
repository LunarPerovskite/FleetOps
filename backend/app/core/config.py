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
    
    # ═══════════════════════════════════════
    # AGENT CONNECTORS (17+ Supported)
    # ═══════════════════════════════════════
    
    # Personal Agents
    OPENCLAW_URL: Optional[str] = None
    OPENCLAW_API_KEY: Optional[str] = None
    OPENCLAW_TIMEOUT: int = 300
    OPENCLAW_MAX_STEPS: int = 50
    
    HERMES_URL: Optional[str] = None
    HERMES_API_KEY: Optional[str] = None
    HERMES_TIMEOUT: int = 300
    HERMES_PERSONA: str = "professional"
    
    # Multi-Agent Frameworks
    CREWAI_URL: Optional[str] = None
    CREWAI_API_KEY: Optional[str] = None
    CREWAI_TIMEOUT: int = 600
    
    AUTOGEN_URL: Optional[str] = None
    AUTOGEN_API_KEY: Optional[str] = None
    AUTOGEN_TIMEOUT: int = 600
    AUTOGEN_MAX_ROUNDS: int = 50
    
    METAGPT_URL: Optional[str] = None
    METAGPT_API_KEY: Optional[str] = None
    METAGPT_TIMEOUT: int = 600
    
    CHATDEV_URL: Optional[str] = None
    CHATDEV_API_KEY: Optional[str] = None
    CHATDEV_TIMEOUT: int = 600
    
    GPTEAM_URL: Optional[str] = None
    GPTEAM_API_KEY: Optional[str] = None
    GPTEAM_TIMEOUT: int = 600
    
    AGENTVERSE_URL: Optional[str] = None
    AGENTVERSE_API_KEY: Optional[str] = None
    AGENTVERSE_TIMEOUT: int = 300
    
    PRAISONAI_URL: Optional[str] = None
    PRAISONAI_API_KEY: Optional[str] = None
    PRAISONAI_TIMEOUT: int = 300
    
    # Agent Frameworks
    LANGCHAIN_URL: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_TIMEOUT: int = 300
    
    LLAMAINDEX_URL: Optional[str] = None
    LLAMAINDEX_API_KEY: Optional[str] = None
    LLAMAINDEX_TIMEOUT: int = 300
    
    TASKWEAVER_URL: Optional[str] = None
    TASKWEAVER_API_KEY: Optional[str] = None
    TASKWEAVER_TIMEOUT: int = 300
    
    # Autonomous Agents
    BABYAGI_URL: Optional[str] = None
    BABYAGI_API_KEY: Optional[str] = None
    BABYAGI_TIMEOUT: int = 300
    
    SUPERAGI_URL: Optional[str] = None
    SUPERAGI_API_KEY: Optional[str] = None
    SUPERAGI_TIMEOUT: int = 600
    
    # Local LLM
    OLLAMA_URL: Optional[str] = None
    OLLAMA_MODEL: str = "llama2"
    
    LOCAL_LLM_URL: Optional[str] = None
    LOCAL_LLM_MODEL: Optional[str] = None
    LOCAL_LLM_TIMEOUT: int = 120
    
    # Custom
    CUSTOM_AGENT_URL: Optional[str] = None
    CUSTOM_AGENT_API_KEY: Optional[str] = None
    
    # Agent Execution Settings
    AGENT_AUTO_APPROVE_LOW_RISK: bool = False
    AGENT_MAX_EXECUTION_TIME: int = 3600
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Evidence store
    EVIDENCE_HOT_DAYS: int = 90
    EVIDENCE_COLD_DAYS: int = 365
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
