"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="HA Config Manager", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=4, alias="WORKERS")

    # Security
    secret_key: str = Field(..., alias="SECRET_KEY")
    encryption_key: Optional[str] = Field(default=None, alias="ENCRYPTION_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    database_pool_size: int = Field(default=20, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND"
    )

    # GitHub
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    github_webhook_secret: Optional[str] = Field(default=None, alias="GITHUB_WEBHOOK_SECRET")
    github_repo_owner: Optional[str] = Field(default=None, alias="GITHUB_REPO_OWNER")
    github_repo_name: Optional[str] = Field(default=None, alias="GITHUB_REPO_NAME")

    # Tailscale
    tailscale_api_key: Optional[str] = Field(default=None, alias="TAILSCALE_API_KEY")
    tailscale_tailnet: Optional[str] = Field(default=None, alias="TAILSCALE_TAILNET")

    # AI (OpenRouter / Deepseek)
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    ai_model: str = Field(default="deepseek/deepseek-chat", alias="AI_MODEL")
    ai_max_tokens: int = Field(default=4000, alias="AI_MAX_TOKENS")
    ai_temperature: float = Field(default=0.7, alias="AI_TEMPERATURE")

    # MinIO / S3
    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    minio_bucket: str = Field(default="ha-config-backups", alias="MINIO_BUCKET")

    # CORS
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:8123,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as list."""
        return [origin.strip() for origin in self.cors_origins_str.split(",")]

    # Email
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, alias="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="noreply@haconfig.local", alias="SMTP_FROM")

    # Deployment
    backup_before_deploy: bool = Field(default=True, alias="BACKUP_BEFORE_DEPLOY")
    validate_before_deploy: bool = Field(default=True, alias="VALIDATE_BEFORE_DEPLOY")
    max_parallel_deployments: int = Field(default=3, alias="MAX_PARALLEL_DEPLOYMENTS")
    deployment_timeout: int = Field(default=300, alias="DEPLOYMENT_TIMEOUT")

    # Monitoring
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, alias="METRICS_PORT")

    # WebSocket
    ws_heartbeat_interval: int = Field(default=30, alias="WS_HEARTBEAT_INTERVAL")
    ws_max_connections: int = Field(default=100, alias="WS_MAX_CONNECTIONS")

    # Encryption
    encryption_key: Optional[str] = Field(default=None, alias="ENCRYPTION_KEY")

    # Home Assistant
    ha_supervisor_token: Optional[str] = Field(default=None, alias="HA_SUPERVISOR_TOKEN")
    ha_long_lived_token: Optional[str] = Field(default=None, alias="HA_LONG_LIVED_TOKEN")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"

    @property
    def api_v1_prefix(self) -> str:
        """Get API v1 prefix."""
        return "/api/v1"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()
