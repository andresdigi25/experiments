import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "CloudWatch Logs Dashboard API"
    API_V1_STR: str = "/api"
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    
    # If running in AWS, these can be empty and boto3 will use instance profile
    USE_AWS_INSTANCE_PROFILE: bool = os.getenv("USE_AWS_INSTANCE_PROFILE", "False").lower() == "true"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200",  # Angular dev server
        "http://localhost:8080",  # Nginx in Docker
        "http://localhost",
        "http://frontend",        # Docker service name
    ]
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Query Limits
    MAX_LOGS_RESULTS: int = int(os.getenv("MAX_LOGS_RESULTS", "1000"))
    MAX_QUERY_DURATION_SECONDS: int = int(os.getenv("MAX_QUERY_DURATION_SECONDS", "300"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()