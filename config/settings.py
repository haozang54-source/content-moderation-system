"""系统配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """系统配置"""

    # LLM配置
    deepseek_api_key: str = ""
    openai_api_key: Optional[str] = None

    # OCR配置
    tencent_secret_id: Optional[str] = None
    tencent_secret_key: Optional[str] = None

    # 数据库配置
    database_url: str = "sqlite:///./data/moderation.db"
    redis_url: str = "redis://localhost:6379/0"

    # 系统配置
    confidence_threshold_high: float = 0.9
    confidence_threshold_low: float = 0.6
    max_workers: int = 4
    log_level: str = "INFO"

    # Celery配置
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
