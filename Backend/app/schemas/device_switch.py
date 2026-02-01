"""
디바이스 스위치 상태 Pydantic 스키마
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class DeviceSwitchResponse(BaseModel):
    """디바이스 스위치 상태 응답 스키마"""
    id: int
    device_mac: str
    desired_state: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceSwitchListResponse(BaseModel):
    """디바이스 스위치 상태 목록 응답 스키마"""
    items: List[DeviceSwitchResponse]
    total: int
