"""
WebSocket 엔드포인트
실시간 디바이스 상태 스트리밍을 제공합니다.
"""

import asyncio
import json
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import async_session
from app.models.device import Device

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """WebSocket 연결 관리 클래스"""

    def __init__(self):
        # 활성 WebSocket 연결 목록
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """새로운 WebSocket 연결을 수락하고 목록에 추가합니다."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결을 목록에서 제거합니다."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """모든 활성 연결에 메시지를 브로드캐스트합니다."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # 연결이 끊긴 클라이언트 제거
        for conn in disconnected:
            self.active_connections.remove(conn)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """특정 클라이언트에게 메시지를 전송합니다."""
        await websocket.send_json(message)


# 전역 연결 관리자 인스턴스
manager = ConnectionManager()


async def get_all_device_status() -> list:
    """모든 디바이스의 현재 상태를 조회합니다."""
    async with async_session() as session:
        result = await session.execute(select(Device))
        devices = result.scalars().all()
        return [
            {
                "id": device.id,
                "name": device.name,
                "location": device.location,
                "is_active": device.is_active,
                "current_power": device.current_power,
                "temperature": device.temperature,
                "is_online": device.is_online,
            }
            for device in devices
        ]


@router.websocket("/ws/devices")
async def websocket_devices(websocket: WebSocket):
    """
    디바이스 실시간 상태 스트리밍 WebSocket 엔드포인트
    연결된 클라이언트에게 주기적으로 디바이스 상태를 전송합니다.
    """
    await manager.connect(websocket)
    try:
        while True:
            try:
                # 클라이언트로부터 메시지 수신 (ping/pong 또는 제어 명령)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                # 클라이언트 메시지 처리 (향후 확장 가능)
                message = json.loads(data)
                if message.get("type") == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
            except asyncio.TimeoutError:
                pass

            # 모든 디바이스 상태를 조회하여 브로드캐스트
            devices_status = await get_all_device_status()
            await manager.send_personal_message(
                {
                    "type": "device_status",
                    "data": devices_status,
                },
                websocket,
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
