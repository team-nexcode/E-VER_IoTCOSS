"""
WebSocket 엔드포인트
실시간 디바이스 상태 스트리밍 + MQTT 메시지 전달
"""

import asyncio
import json
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select, desc

from app.database import async_session
from app.models.device import Device
from app.config import get_settings

settings = get_settings()
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
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)


# 전역 연결 관리자 인스턴스
manager = ConnectionManager()


async def get_all_device_status() -> list:
    """최근 디바이스 센서 데이터를 조회합니다."""
    async with async_session() as session:
        result = await session.execute(
            select(Device).order_by(desc(Device.id)).limit(20)
        )
        devices = result.scalars().all()
        return [
            {
                "id": device.id,
                "device_name": device.device_name,
                "device_mac": device.device_mac,
                "temperature": device.temperature,
                "humidity": device.humidity,
                "energy_amp": device.energy_amp,
                "relay_status": device.relay_status,
                "timestamp": str(device.timestamp) if device.timestamp else None,
            }
            for device in devices
        ]


async def broadcast_mqtt_message(topic: str, payload) -> None:
    """MQTT 메시지를 모든 WebSocket 클라이언트에 전달합니다."""
    await manager.broadcast({
        "type": "mqtt_message",
        "broker": f"mqtt://{settings.MQTT_BROKER}:{settings.MQTT_PORT}",
        "topic": topic,
        "subscribe_filter": settings.MQTT_TOPIC,
        "payload": payload,
    })


@router.websocket("/ws/devices")
async def websocket_devices(websocket: WebSocket):
    """
    디바이스 실시간 상태 스트리밍 WebSocket 엔드포인트
    - 연결 시 현재 디바이스 상태 1회 전송
    - 이후 클라이언트 ping 에만 응답 (MQTT 메시지는 broadcast로 전달)
    """
    await manager.connect(websocket)

    # 연결 직후 현재 디바이스 상태 1회 전송
    devices_status = await get_all_device_status()
    await manager.send_personal_message(
        {"type": "device_status", "data": devices_status},
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
