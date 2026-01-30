"""
IoTCOSS 백엔드 FastAPI 앱 진입점
애플리케이션 인스턴스를 생성하고 미들웨어, 라우터, 이벤트를 설정합니다.
"""

import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base

# API 라우터 import
from app.api.devices import router as devices_router
from app.api.power import router as power_router
from app.api.auth import router as auth_router
from app.api.websocket import router as websocket_router
from app.api.mobius import router as mobius_router
from app.api.api_logs import router as api_logs_router

# 서비스 import
from app.services.mqtt_service import mqtt_service
from app.services.mobius_service import mobius_service

settings = get_settings()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    앱 시작/종료 시 실행되는 lifespan 이벤트 핸들러
    - 시작: DB 테이블 생성, MQTT 브로커 연결
    - 종료: MQTT 연결 해제, DB 엔진 종료
    """
    # === 앱 시작 시 ===
    logger.info("IoTCOSS 백엔드 서버를 시작합니다...")

    # 데이터베이스 테이블 생성 (개발 환경용, 운영에서는 Alembic 사용 권장)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("데이터베이스 테이블 초기화 완료")

    # MQTT 브로커 연결 시도
    try:
        await mqtt_service.connect()
        if mqtt_service.is_connected:
            logger.info("MQTT 브로커 연결 완료")
    except Exception as e:
        logger.warning(f"MQTT 브로커 연결 실패 (서버는 계속 실행됩니다): {e}")

    yield

    # === 앱 종료 시 ===
    logger.info("IoTCOSS 백엔드 서버를 종료합니다...")

    # MQTT 연결 해제
    await mqtt_service.disconnect()

    # Mobius HTTP 클라이언트 종료
    await mobius_service.close()

    # DB 엔진 종료
    await engine.dispose()
    logger.info("서버 종료 완료")


# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="IoT 기반 스마트 콘센트 관리 시스템 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 미들웨어 설정 (React 개발 서버 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://iotcoss.nexcode.kr",
        "http://iotcoss.nexcode.kr:5173",
        "https://iotcoss.nexcode.kr",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 라우터 등록
app.include_router(devices_router)
app.include_router(power_router)
app.include_router(auth_router)
app.include_router(websocket_router)
app.include_router(mobius_router)
app.include_router(api_logs_router)


@app.get("/api/health", tags=["헬스체크"])
async def health_check():
    """
    서버 헬스체크 엔드포인트
    서버 상태 및 MQTT 연결 상태를 반환합니다.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "mqtt_connected": mqtt_service.is_connected,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }
