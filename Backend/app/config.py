"""
IoTCOSS 백엔드 환경 설정 모듈
pydantic-settings를 사용하여 .env 파일에서 환경 변수를 로드합니다.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""

    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/iotcoss"

    # Redis 설정
    REDIS_URL: str = "redis://localhost:6379"

    # MQTT 브로커 설정
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883

    # JWT 인증 설정
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # 앱 기본 설정
    APP_NAME: str = "IoTCOSS API"
    DEBUG: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스를 캐싱하여 반환합니다."""
    return Settings()
