"""
Application configuration — reads from environment / .env file.
Single source of truth for all settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "DMS"
    app_version: str = "0.1.0"
    app_env: str = "development"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://dms:dms_secret@localhost:5432/dms"

    # JWT
    secret_key: str = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Company info (shown on invoices + login)
    company_name: str = "DMS Company"
    company_address: str = "Dhaka, Bangladesh"
    company_phone: str = "+8801XXXXXXXXX"
    company_vat_bin: str = "XXXXXXXXXX-XXXX"

    # SMS (Sprint 7)
    sms_api_key: str = ""
    sms_sender_id: str = ""
    sms_base_url: str = "https://sms.sslwireless.com"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
