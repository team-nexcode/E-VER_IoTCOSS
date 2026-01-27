"""
디바이스 비즈니스 로직 서비스
디바이스 관련 데이터베이스 작업과 비즈니스 로직을 처리합니다.
"""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate

logger = logging.getLogger(__name__)


class DeviceService:
    """디바이스 관련 비즈니스 로직 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_devices(self) -> List[Device]:
        """
        모든 디바이스 목록을 조회합니다.

        Returns:
            등록된 전체 디바이스 리스트
        """
        result = await self.db.execute(select(Device).order_by(Device.id))
        devices = result.scalars().all()
        return list(devices)

    async def get_device(self, device_id: int) -> Optional[Device]:
        """
        특정 디바이스를 ID로 조회합니다.

        Args:
            device_id: 조회할 디바이스 ID

        Returns:
            디바이스 객체 또는 None
        """
        result = await self.db.execute(select(Device).where(Device.id == device_id))
        return result.scalar_one_or_none()

    async def create_device(self, device_data: DeviceCreate) -> Device:
        """
        새로운 디바이스를 등록합니다.

        Args:
            device_data: 디바이스 생성 데이터

        Returns:
            생성된 디바이스 객체
        """
        new_device = Device(
            name=device_data.name,
            location=device_data.location,
            mqtt_topic=device_data.mqtt_topic,
        )
        self.db.add(new_device)
        await self.db.flush()
        await self.db.refresh(new_device)
        logger.info(f"디바이스 생성: {new_device.name} (ID: {new_device.id})")
        return new_device

    async def update_device(self, device_id: int, device_data: DeviceUpdate) -> Optional[Device]:
        """
        디바이스 정보를 수정합니다.

        Args:
            device_id: 수정할 디바이스 ID
            device_data: 수정할 데이터

        Returns:
            수정된 디바이스 객체 또는 None
        """
        device = await self.get_device(device_id)
        if not device:
            return None

        # 전달된 필드만 업데이트 (None이 아닌 값만)
        update_data = device_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)

        await self.db.flush()
        await self.db.refresh(device)
        logger.info(f"디바이스 수정: {device.name} (ID: {device.id})")
        return device

    async def toggle_device(self, device_id: int) -> Optional[Device]:
        """
        디바이스 전원 상태를 토글합니다 (On ↔ Off).

        Args:
            device_id: 토글할 디바이스 ID

        Returns:
            토글된 디바이스 객체 또는 None
        """
        device = await self.get_device(device_id)
        if not device:
            return None

        # 전원 상태 토글
        device.is_active = not device.is_active
        await self.db.flush()
        await self.db.refresh(device)

        state = "ON" if device.is_active else "OFF"
        logger.info(f"디바이스 토글: {device.name} (ID: {device.id}) → {state}")
        return device

    async def update_device_status(
        self,
        device_id: int,
        power: float,
        temperature: float,
        is_online: bool = True,
    ) -> Optional[Device]:
        """
        디바이스의 실시간 상태를 업데이트합니다.
        MQTT 메시지 수신 시 호출됩니다.

        Args:
            device_id: 디바이스 ID
            power: 현재 전력(W)
            temperature: 현재 온도(°C)
            is_online: 연결 상태

        Returns:
            업데이트된 디바이스 객체 또는 None
        """
        device = await self.get_device(device_id)
        if not device:
            return None

        device.current_power = power
        device.temperature = temperature
        device.is_online = is_online

        await self.db.flush()
        await self.db.refresh(device)
        return device

    async def delete_device(self, device_id: int) -> bool:
        """
        디바이스를 삭제합니다.

        Args:
            device_id: 삭제할 디바이스 ID

        Returns:
            삭제 성공 여부
        """
        device = await self.get_device(device_id)
        if not device:
            return False

        await self.db.delete(device)
        await self.db.flush()
        logger.info(f"디바이스 삭제: {device.name} (ID: {device.id})")
        return True
