from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database
    database_url: str
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Firebase Authentication
    firebase_project_id: str = ""
    # Optional: Path to service account JSON file (for local development without ADC)
    firebase_service_account_path: Optional[str] = None
    
    # Jira Integration (OAuth 2.0)
    jira_base_url: str = ""
    jira_client_id: str = ""
    jira_client_secret: str = ""
    # Cloud ID is needed for OAuth - get from /oauth/token/accessible-resources
    jira_cloud_id: str = ""
    
    # Precursive/Salesforce Integration (OAuth)
    precursive_client_id: str = ""
    precursive_client_secret: str = ""
    precursive_instance_url: str = ""
    
    # Precursive/Salesforce (Alternative: Username/Password flow)
    precursive_username: str = ""
    precursive_password: str = ""
    precursive_security_token: str = ""
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars like NEXT_PUBLIC_* from frontend


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
