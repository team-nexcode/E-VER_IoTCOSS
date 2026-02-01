"""
IoTCOSS 백엔드 FastAPI 앱 진입점
애플리케이션 인스턴스를 생성하고 미들웨어, 라우터, 이벤트를 설정합니다.
"""

import asyncio
import json
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
from app.api.websocket import router as websocket_router, broadcast_mqtt_message, broadcast_system_log, broadcast_device_update, get_cached_device_mac, update_device_last_seen, start_offline_checker
from app.api.mobius import router as mobius_router
from app.api.api_logs import router as api_logs_router
from app.api.system_logs import router as system_logs_router
from app.api.device_mac import router as device_mac_router

# 서비스 import
from app.services.mqtt_service import mqtt_service
from app.services.mobius_service import mobius_service

# DB 세션 (로그 저장용)
from app.database import async_session
from app.models.system_log import SystemLog
from app.models.device import Device

# 모든 모델을 import하여 create_all 시 테이블이 생성되도록 함
import app.models  # noqa: F401

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

    # 오프라인 감지 백그라운드 태스크 시작
    offline_checker_task = start_offline_checker()

    # MQTT 브로커 연결 시도
    mqtt_listen_task = None
    try:
        await mqtt_service.connect()
        if mqtt_service.is_connected:
            logger.info("MQTT 브로커 연결 완료")
            await mqtt_service.subscribe(settings.MQTT_TOPIC)
            logger.info(f"MQTT 토픽 구독: {settings.MQTT_TOPIC}")

            # MQTT 메시지 수신 → 대시보드 즉시 업데이트 + DB 저장/브로드캐스트 병렬 처리
            async def on_mqtt_message(topic: str, payload):
                logger.info(f"MQTT 수신: {topic} → {payload}")

                # payload를 dict로 파싱
                try:
                    data = payload if isinstance(payload, dict) else json.loads(payload)
                except Exception:
                    data = {}

                # oneM2M 구조에서 m2m:cin 객체 추출
                cin = None
                if "pc" in data:
                    sgn = data["pc"].get("m2m:sgn", {})
                    cin = sgn.get("nev", {}).get("rep", {}).get("m2m:cin", {})
                elif "m2m:sgn" in data:
                    cin = data["m2m:sgn"].get("nev", {}).get("rep", {}).get("m2m:cin", {})
                elif "con" in data:
                    cin = data

                # ct(생성시간) 파싱
                parsed_ts = None
                if cin:
                    ct = cin.get("ct")
                    if ct:
                        try:
                            parsed_ts = datetime.strptime(ct, "%Y%m%dT%H%M%S")
                        except Exception:
                            parsed_ts = None

                # ── 디바이스 센서 데이터 파싱 (DB 접근 없이 빠르게) ──
                update_data = None
                mac_addr = None
                if cin:
                    lbl = cin.get("lbl", [])
                    for item in lbl:
                        if isinstance(item, str) and ":" in item and len(item) == 17:
                            mac_addr = item
                            break

                    if mac_addr:
                        mac_info = await get_cached_device_mac(mac_addr)
                        if mac_info:
                            update_device_last_seen(mac_addr)

                            con = cin.get("con", {})
                            if isinstance(con, str):
                                try:
                                    con = json.loads(con)
                                except Exception:
                                    con = {}

                            update_data = {
                                "device_mac": mac_addr,
                                "device_name": mac_info["device_name"],
                                "location": mac_info["location"],
                                "temperature": float(con["temp"]) if "temp" in con else None,
                                "humidity": float(con["humi"]) if "humi" in con else None,
                                "energy_amp": float(con["energy"]) if "energy" in con else None,
                                "relay_status": str(con["status"]) if "status" in con else None,
                                "timestamp": str(parsed_ts) if parsed_ts else None,
                                "is_online": True,
                            }

                # ── FAST PATH: 대시보드 업데이트를 최우선 브로드캐스트 ──
                if update_data:
                    await broadcast_device_update(update_data)

                # ── DB 저장 + 나머지 브로드캐스트 병렬 처리 ──
                mqtt_detail = json.dumps({
                    "broker": f"mqtt://{settings.MQTT_BROKER}:{settings.MQTT_PORT}",
                    "topic": topic,
                    "subscribe_filter": settings.MQTT_TOPIC,
                    "payload": payload,
                }, ensure_ascii=False)

                sensor_detail = None
                sensor_message = None
                if update_data:
                    sensor_detail = json.dumps({
                        "table": "devices",
                        "action": "INSERT",
                        "device_name": update_data["device_name"],
                        "device_mac": update_data["device_mac"],
                        "temperature": update_data["temperature"],
                        "humidity": update_data["humidity"],
                        "energy_amp": update_data["energy_amp"],
                        "relay_status": update_data["relay_status"],
                        "timestamp": update_data["timestamp"],
                    }, ensure_ascii=False)
                    sensor_message = f"[devices] INSERT: {update_data['device_name']} ({update_data['device_mac']})"

                async def _save_to_db():
                    try:
                        async with async_session() as session:
                            # MQTT 수신 로그
                            mqtt_log = SystemLog(
                                type="MESSAGE", level="info", source="MQTT",
                                message=f"토픽: {topic}", detail=mqtt_detail,
                            )
                            if parsed_ts:
                                mqtt_log.timestamp = parsed_ts
                            session.add(mqtt_log)

                            # 디바이스 센서 데이터 + 센서 로그
                            if update_data:
                                device_entry = Device(
                                    device_name=update_data["device_name"],
                                    device_mac=update_data["device_mac"],
                                    temperature=update_data["temperature"],
                                    humidity=update_data["humidity"],
                                    energy_amp=update_data["energy_amp"],
                                    relay_status=update_data["relay_status"],
                                    timestamp=parsed_ts,
                                )
                                session.add(device_entry)

                                sensor_log = SystemLog(
                                    type="SYSTEM", level="info", source="App",
                                    message=sensor_message, detail=sensor_detail,
                                )
                                if parsed_ts:
                                    sensor_log.timestamp = parsed_ts
                                session.add(sensor_log)

                            await session.commit()
                    except Exception as e:
                        logger.error(f"DB 저장 실패: {e}")

                # 병렬 실행: DB 저장 + 브로드캐스트들
                tasks = [_save_to_db(), broadcast_mqtt_message(topic, payload)]
                if update_data:
                    tasks.append(broadcast_system_log(message=sensor_message, detail=sensor_detail))

                await asyncio.gather(*tasks)

            mqtt_service.set_message_handler(on_mqtt_message)
            mqtt_listen_task = asyncio.create_task(mqtt_service.listen())
            logger.info("MQTT 리스너 시작")
    except Exception as e:
        logger.warning(f"MQTT 브로커 연결 실패 (서버는 계속 실행됩니다): {e}")

    yield

    if mqtt_listen_task:
        mqtt_listen_task.cancel()
    offline_checker_task.cancel()

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
app.include_router(system_logs_router)
app.include_router(device_mac_router)


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
        "mqtt_broker": f"mqtt://{settings.MQTT_BROKER}:{settings.MQTT_PORT}",
        "mqtt_topic": settings.MQTT_TOPIC,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }
