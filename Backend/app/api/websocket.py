"""
WebSocket 엔드포인트
실시간 디바이스 상태 스트리밍 + MQTT 메시지 전달
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select, desc, func

from app.database import async_session
from app.models.device import Device
from app.models.device_mac import DeviceMac
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

OFFLINE_THRESHOLD = 30  # 초
VOLTAGE = 220  # AC 전압
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """WebSocket 연결 관리 클래스"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return

        async def _safe_send(conn: WebSocket) -> bool:
            try:
                await conn.send_json(message)
                return True
            except Exception:
                return False

        results = await asyncio.gather(
            *[_safe_send(conn) for conn in self.active_connections]
        )
        to_remove = [
            self.active_connections[i]
            for i, ok in enumerate(results)
            if not ok
        ]
        for conn in to_remove:
            self.active_connections.remove(conn)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)


# 전역 연결 관리자 인스턴스
manager = ConnectionManager()

# device_mac 캐시 (MAC → {device_name, location})
_device_mac_cache: dict[str, dict] = {}

# 디바이스 마지막 수신 시각 (MAC → time.time())
_device_last_seen: dict[str, float] = {}


def update_device_last_seen(mac: str) -> None:
    """MQTT 센서 데이터 수신 시 마지막 수신 시각을 갱신합니다."""
    _device_last_seen[mac] = time.time()


def is_device_online(mac: str) -> bool:
    """마지막 수신으로부터 OFFLINE_THRESHOLD 이내면 온라인으로 판정합니다."""
    last = _device_last_seen.get(mac)
    if last is None:
        return False
    return (time.time() - last) <= OFFLINE_THRESHOLD


async def get_cached_device_mac(mac_addr: str) -> dict | None:
    """device_mac 테이블을 캐시하여 빠르게 조회합니다. 캐시 미스 시 DB 조회."""
    if mac_addr in _device_mac_cache:
        return _device_mac_cache[mac_addr]
    async with async_session() as session:
        result = await session.execute(
            select(DeviceMac).where(DeviceMac.device_mac == mac_addr)
        )
        entry = result.scalar_one_or_none()
        if entry:
            info = {"device_name": entry.device_name, "location": entry.location}
            _device_mac_cache[mac_addr] = info
            return info
    return None


def invalidate_device_mac_cache() -> None:
    """device_mac CRUD 시 캐시를 무효화합니다."""
    _device_mac_cache.clear()


# ── 전력량 계산 ──

async def calculate_energy_kwh(start_time: datetime, end_time: datetime) -> float:
    """주어진 기간의 총 전력량(kWh)을 사다리꼴 적분으로 계산합니다."""
    async with async_session() as session:
        result = await session.execute(
            select(Device.device_mac, Device.energy_amp, Device.timestamp)
            .where(Device.timestamp >= start_time)
            .where(Device.timestamp <= end_time)
            .where(Device.energy_amp.isnot(None))
            .where(Device.timestamp.isnot(None))
            .order_by(Device.device_mac, Device.timestamp)
        )
        rows = result.all()

    if not rows:
        return 0.0

    total_wh = 0.0
    prev_mac = None
    prev_amp = 0.0
    prev_ts = None

    for mac, amp, ts in rows:
        if mac == prev_mac and prev_ts is not None:
            dt_hours = (ts - prev_ts).total_seconds() / 3600
            if 0 < dt_hours < 1:
                total_wh += ((prev_amp + amp) / 2) * VOLTAGE * dt_hours
        prev_mac = mac
        prev_amp = amp
        prev_ts = ts

    return total_wh / 1000


async def get_power_summary() -> dict:
    """이번 달 / 어제 / 오늘 전력량(kWh)을 반환합니다."""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    month_start = today_start.replace(day=1)

    today_kwh = get_today_energy_kwh()
    monthly_energy, yesterday_energy = await asyncio.gather(
        calculate_energy_kwh(month_start, now),
        calculate_energy_kwh(yesterday_start, today_start),
    )

    return {
        "monthly_energy_kwh": round(monthly_energy, 4),
        "yesterday_energy_kwh": round(yesterday_energy, 4),
        "today_energy_kwh": round(today_kwh, 4),
    }


# ── 오늘 전력량 실시간 누적기 ──

_today_energy_wh: float = 0.0
_today_date: object = None  # date
_last_energy_readings: dict[str, tuple[float, datetime]] = {}


async def init_energy_accumulator() -> None:
    """서버 시작 시 오늘 전력량을 DB에서 계산하여 누적기를 초기화합니다."""
    global _today_energy_wh, _today_date, _last_energy_readings
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    _today_energy_wh = (await calculate_energy_kwh(today_start, now)) * 1000
    _today_date = now.date()
    _last_energy_readings = {}

    # 디바이스별 마지막 읽기값 로드 (이후 증분 계산용)
    async with async_session() as session:
        subq = (
            select(Device.device_mac, func.max(Device.id).label("max_id"))
            .where(Device.timestamp >= today_start)
            .where(Device.energy_amp.isnot(None))
            .group_by(Device.device_mac)
            .subquery()
        )
        result = await session.execute(
            select(Device.device_mac, Device.energy_amp, Device.timestamp)
            .join(subq, (Device.device_mac == subq.c.device_mac) & (Device.id == subq.c.max_id))
        )
        for mac, amp, ts in result.all():
            if amp is not None and ts is not None:
                _last_energy_readings[mac] = (amp, ts)

    logger.info(f"전력량 누적기 초기화 완료: {_today_energy_wh:.1f} Wh")


def accumulate_energy(mac: str, energy_amp: float | None, timestamp: datetime | None) -> float:
    """새 센서 데이터로 오늘 전력량을 증분 누적합니다. 현재 오늘 kWh를 반환합니다."""
    global _today_energy_wh, _today_date, _last_energy_readings

    today = datetime.now().date()
    if _today_date != today:
        _today_energy_wh = 0.0
        _today_date = today
        _last_energy_readings = {}

    if energy_amp is None or timestamp is None:
        return _today_energy_wh / 1000

    last = _last_energy_readings.get(mac)
    if last:
        last_amp, last_ts = last
        dt_hours = (timestamp - last_ts).total_seconds() / 3600
        if 0 < dt_hours < 1:
            _today_energy_wh += ((last_amp + energy_amp) / 2) * VOLTAGE * dt_hours

    _last_energy_readings[mac] = (energy_amp, timestamp)
    return _today_energy_wh / 1000


def get_today_energy_kwh() -> float:
    """현재 누적된 오늘 전력량(kWh)을 반환합니다."""
    if _today_date != datetime.now().date():
        return 0.0
    return _today_energy_wh / 1000


async def get_all_device_status() -> list:
    """device_mac 테이블 기반으로 전체 디바이스 목록 + 최신 센서 데이터를 조회합니다."""
    async with async_session() as session:
        # device_mac 전체 목록 조회
        mac_result = await session.execute(
            select(DeviceMac).order_by(DeviceMac.id)
        )
        mac_entries = mac_result.scalars().all()

        # 각 MAC별 최신 devices 레코드의 id를 서브쿼리로 조회
        latest_subq = (
            select(
                Device.device_mac,
                func.max(Device.id).label("max_id"),
            )
            .group_by(Device.device_mac)
            .subquery()
        )

        # 최신 레코드들을 한 번에 조회
        latest_result = await session.execute(
            select(Device).join(
                latest_subq,
                (Device.device_mac == latest_subq.c.device_mac)
                & (Device.id == latest_subq.c.max_id),
            )
        )
        latest_devices = {d.device_mac: d for d in latest_result.scalars().all()}

        result = []
        for mac in mac_entries:
            latest = latest_devices.get(mac.device_mac)
            result.append({
                "id": mac.id,
                "device_name": mac.device_name,
                "device_mac": mac.device_mac,
                "location": mac.location,
                "temperature": latest.temperature if latest else None,
                "humidity": latest.humidity if latest else None,
                "energy_amp": latest.energy_amp if latest else None,
                "relay_status": latest.relay_status if latest else None,
                "is_online": is_device_online(mac.device_mac),
                "timestamp": str(latest.timestamp) if latest and latest.timestamp else None,
            })

        return result


async def broadcast_mqtt_message(topic: str, payload) -> None:
    """MQTT 메시지를 모든 WebSocket 클라이언트에 전달합니다."""
    await manager.broadcast({
        "type": "mqtt_message",
        "broker": f"mqtt://{settings.MQTT_BROKER}:{settings.MQTT_PORT}",
        "topic": topic,
        "subscribe_filter": settings.MQTT_TOPIC,
        "payload": payload,
    })


async def broadcast_system_log(message: str, detail: str | None = None, level: str = "info", source: str = "App") -> None:
    """시스템 로그를 모든 WebSocket 클라이언트에 실시간 전달합니다."""
    await manager.broadcast({
        "type": "system_log",
        "log": {
            "type": "SYSTEM",
            "level": level,
            "source": source,
            "message": message,
            "detail": detail,
        },
    })


async def broadcast_device_update(data: dict) -> None:
    """디바이스 센서 데이터 업데이트를 모든 WebSocket 클라이언트에 실시간 전달합니다."""
    await manager.broadcast({"type": "device_update", "data": data})


# ── 오프라인 감지 백그라운드 태스크 ──

_previously_online: set[str] = set()


async def _offline_checker_loop() -> None:
    """5초마다 오프라인 전환된 디바이스를 감지하여 클라이언트에 브로드캐스트합니다."""
    global _previously_online
    while True:
        await asyncio.sleep(5)
        try:
            now = time.time()
            currently_online: set[str] = set()
            for mac, last in _device_last_seen.items():
                if now - last <= OFFLINE_THRESHOLD:
                    currently_online.add(mac)

            newly_offline = _previously_online - currently_online
            for mac in newly_offline:
                mac_info = _device_mac_cache.get(mac)
                await broadcast_device_update({
                    "device_mac": mac,
                    "device_name": mac_info["device_name"] if mac_info else "",
                    "location": mac_info["location"] if mac_info else "",
                    "is_online": False,
                })
                logger.info(f"디바이스 오프라인 전환: {mac}")

            _previously_online = currently_online
        except Exception as e:
            logger.error(f"오프라인 체커 오류: {e}")


def start_offline_checker() -> asyncio.Task:
    """오프라인 감지 백그라운드 태스크를 시작합니다."""
    return asyncio.create_task(_offline_checker_loop())


@router.websocket("/ws/devices")
async def websocket_devices(websocket: WebSocket):
    """
    디바이스 실시간 상태 스트리밍 WebSocket 엔드포인트
    - 연결 시 현재 디바이스 상태 1회 전송
    - 이후 클라이언트 ping 에만 응답 (MQTT 메시지는 broadcast로 전달)
    """
    await manager.connect(websocket)

    # 연결 직후 현재 디바이스 상태 + 전력량 요약 1회 전송
    devices_status, power_summary = await asyncio.gather(
        get_all_device_status(),
        get_power_summary(),
    )
    await manager.send_personal_message(
        {"type": "device_status", "data": devices_status},
        websocket,
    )
    await manager.send_personal_message(
        {"type": "power_summary", "data": power_summary},
        websocket,
    )

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
