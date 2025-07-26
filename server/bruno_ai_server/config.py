"""
Configuration module using pydantic-settings for environment variable management.
"""
import json

from pydantic import ConfigDict, Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database Configuration
    db_url: str = Field(..., description="Database connection URL")

    # Authentication
    jwt_secret: str = Field(..., description="JWT secret key")
    app_secret_key: str = Field(..., description="Application secret key")

    # Google Cloud Platform
    gcp_credentials_json: str = Field(default="{}", description="GCP service account credentials JSON")
    gcp_project_id: str | None = Field(default=None, description="GCP project ID")
    
    # Firebase
    firebase_web_api_key: str | None = Field(default=None, description="Firebase Web API Key for REST authentication")

    # Third-party APIs
    instacart_api_key: str | None = Field(default=None, description="Instacart API key")
    mem0_api_key: str | None = Field(default=None, description="Mem0 API key")
    voxtral_api_key: str | None = Field(default=None, description="Voxtral API key for STT")
    
    # TTS Provider APIs
    elevenlabs_api_key: str | None = Field(default=None, description="ElevenLabs API key for TTS")
    aws_access_key_id: str | None = Field(default=None, description="AWS access key for Polly TTS")
    aws_secret_access_key: str | None = Field(default=None, description="AWS secret key for Polly TTS")
    aws_region: str = Field(default="us-east-1", description="AWS region for Polly TTS")

    # AI/ML APIs
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")

    # Cache/Session
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload")
    log_level: str = Field(default="info", description="Logging level")

    # Environment
    environment: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=False, description="Debug mode")

    @validator("gcp_credentials_json")
    def validate_gcp_credentials(cls, v):
        """Validate that GCP credentials is valid JSON."""
        try:
            json.loads(v)
        except json.JSONDecodeError:
            raise ValueError("GCP_CREDENTIALS_JSON must be valid JSON")
        return v

    @validator("port")
    def validate_port(cls, v):
        """Validate port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ["critical", "error", "warning", "info", "debug"]
        if v.lower() not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v.lower()

    @property
    def gcp_credentials_dict(self) -> dict:
        """Get GCP credentials as a dictionary."""
        return json.loads(self.gcp_credentials_json)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
