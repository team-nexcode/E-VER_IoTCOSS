"""
IoTCOSS 백엔드 FastAPI 앱 진입점
애플리케이션 인스턴스를 생성하고 미들웨어, 라우터, 이벤트를 설정합니다.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base

# API 라우터 import
from app.api.devices import router as devices_router
from app.api.power import router as power_router
from app.api.auth import router as auth_router
from app.api.websocket import router as websocket_router, broadcast_mqtt_message, broadcast_system_log, broadcast_device_update, get_cached_device_mac, update_device_last_seen, start_offline_checker, init_energy_accumulator, accumulate_energy, calculate_energy_kwh, update_dashboard_from_accumulator, KST
from app.api.mobius import router as mobius_router
from app.api.api_logs import router as api_logs_router
from app.api.system_logs import router as system_logs_router
from app.api.device_mac import router as device_mac_router
from app.api.schedules import router as schedules_router
from app.api.ai_analysis import router as ai_router

# 서비스 import
from app.services.mqtt_service import mqtt_service
from app.services.mobius_service import mobius_service
from app.services.schedule_service import schedule_service
from app.services.ai_auto_control_service import start_ai_auto_control_service

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

    # 전력량 누적기 초기화 + 오프라인 감지 백그라운드 태스크 시작
    try:
        await init_energy_accumulator()
    except Exception as e:
        logger.error(f"전력량 누적기 초기화 실패 (서버는 계속 실행됩니다): {e}")
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

                            energy_amp = float(con["energy"]) if "energy" in con else None

                            # 오늘 전력량 실시간 누적
                            today_kwh = accumulate_energy(mac_addr, energy_amp, parsed_ts)

                            update_data = {
                                "device_mac": mac_addr,
                                "device_name": mac_info["device_name"],
                                "location": mac_info["location"],
                                "temperature": float(con["temp"]) if "temp" in con else None,
                                "humidity": float(con["humi"]) if "humi" in con else None,
                                "energy_amp": energy_amp,
                                "relay_status": str(con["status"]) if "status" in con else None,
                                "timestamp": str(parsed_ts) if parsed_ts else None,
                                "is_online": True,
                                "today_energy_kwh": round(today_kwh, 4),
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
                                # MQTT로 수신한 데이터는 아두이노의 "실제 상태"를 반영
                                # desired_state(우리가 보낸 명령)와 별개로 저장
                                device_entry = Device(
                                    device_name=update_data["device_name"],
                                    device_mac=update_data["device_mac"],
                                    temperature=update_data["temperature"],
                                    humidity=update_data["humidity"],
                                    energy_amp=update_data["energy_amp"],
                                    relay_status=update_data["relay_status"],  # 실제 상태
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
                    tasks.append(update_dashboard_from_accumulator())

                await asyncio.gather(*tasks)

            mqtt_service.set_message_handler(on_mqtt_message)
            mqtt_listen_task = asyncio.create_task(mqtt_service.listen())
            logger.info("MQTT 리스너 시작")
    except Exception as e:
        logger.warning(f"MQTT 브로커 연결 실패 (서버는 계속 실행됩니다): {e}")

    # 스케줄 서비스 시작
    schedule_task = asyncio.create_task(schedule_service.start())
    logger.info("스케줄 서비스 시작")

    # AI 자동 제어 서비스 시작 (60분 주기)
    ai_control_task = asyncio.create_task(start_ai_auto_control_service(interval_seconds=10))
    logger.info("AI 자동 제어 서비스 시작 (60분 주기)")

    yield

    if mqtt_listen_task:
        mqtt_listen_task.cancel()
    offline_checker_task.cancel()
    schedule_task.cancel()
    ai_control_task.cancel()
    await schedule_service.stop()

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
app.include_router(schedules_router)
app.include_router(ai_router)


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


@app.get("/api/debug/energy", tags=["디버그"])
async def debug_energy():
    """전력량 계산 진단 엔드포인트 — 날짜별 레코드 수, 계산 결과 확인용"""
    from sqlalchemy import select, func, text
    from app.models.device import Device as DeviceModel

    now = datetime.now(KST)
    today = now.date()
    yesterday = today - timedelta(days=1)
    month_start = today.replace(day=1)

    # 날짜별 레코드 수 조회
    async with async_session() as session:
        date_counts = await session.execute(text(
            "SELECT DATE(timestamp) as d, COUNT(*) as cnt, "
            "COUNT(energy_amp) as amp_cnt "
            "FROM devices WHERE timestamp IS NOT NULL "
            "GROUP BY DATE(timestamp) ORDER BY d DESC LIMIT 10"
        ))
        date_rows = [
            {"date": str(r[0]), "total": r[1], "with_energy_amp": r[2]}
            for r in date_counts.all()
        ]

        # 어제 데이터 샘플 (디바이스별)
        yesterday_detail = await session.execute(text(
            f"SELECT device_mac, COUNT(*) as cnt, "
            f"MIN(energy_amp) as min_amp, MAX(energy_amp) as max_amp, "
            f"MIN(timestamp) as first_ts, MAX(timestamp) as last_ts "
            f"FROM devices "
            f"WHERE DATE(timestamp) = '{yesterday}' AND energy_amp IS NOT NULL "
            f"GROUP BY device_mac ORDER BY device_mac"
        ))
        yesterday_devices = [
            {
                "mac": r[0], "count": r[1],
                "min_amp": float(r[2]) if r[2] else None,
                "max_amp": float(r[3]) if r[3] else None,
                "first_ts": str(r[4]), "last_ts": str(r[5]),
            }
            for r in yesterday_detail.all()
        ]

    # 전력량 계산 결과
    yesterday_kwh = await calculate_energy_kwh(yesterday)
    monthly_kwh = await calculate_energy_kwh(month_start, today)

    return {
        "server_time": str(now),
        "server_date": str(today),
        "yesterday_date": str(yesterday),
        "month_start": str(month_start),
        "date_record_counts": date_rows,
        "yesterday_devices": yesterday_devices,
        "yesterday_kwh": round(yesterday_kwh, 6),
        "monthly_kwh": round(monthly_kwh, 6),
    }
