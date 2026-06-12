import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ReviveIQ - AI Revenue Recovery Agent"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "supersecret_revenue_recovery_key_replace_in_prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database (PostgreSQL only)
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/reviveiq"
    
    # Redis & Celery
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Microsoft Integrations (Placeholder/Optional keys for the enterprise agent)
    MICROSOFT_TENANT_ID: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_GRAPH_ENDPOINT: str = "https://graph.microsoft.com/v1.0"
    
    # Copilot settings
    COPILOT_AGENT_ID: str = "reviveiq-copilot-agent"
    
    # Revenue Rescue Threshold
    RESCUE_CAMPAIGN_THRESHOLD: float = 0.50
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
