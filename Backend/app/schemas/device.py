"""
디바이스 센서 데이터 Pydantic 스키마
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DeviceResponse(BaseModel):
    """디바이스 센서 데이터 응답 스키마"""
    id: int
    device_name: str
    device_mac: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    energy_amp: Optional[float] = None
    relay_status: Optional[str] = None
    timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceListResponse(BaseModel):
    """디바이스 센서 데이터 목록 응답 스키마"""
    items: List[DeviceResponse]
    total: int
