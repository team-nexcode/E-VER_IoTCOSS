"""
디바이스 센서 데이터 서비스
디바이스 센서 데이터 조회를 처리합니다.
"""

import logging
from typing import List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device

logger = logging.getLogger(__name__)


class DeviceService:
    """디바이스 센서 데이터 서비스 클래스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_devices(self, limit: int = 100, offset: int = 0) -> tuple[List[Device], int]:
        """센서 데이터 목록을 조회합니다."""
        count_result = await self.db.execute(select(func.count(Device.id)))
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(Device).order_by(desc(Device.id)).offset(offset).limit(limit)
        )
        devices = list(result.scalars().all())
        return devices, total
