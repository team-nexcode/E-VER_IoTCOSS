"""
디바이스 Pydantic 스키마
API 요청/응답 데이터의 유효성 검사 및 직렬화를 담당합니다.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    """디바이스 기본 스키마 (공통 필드)"""
    name: str = Field(..., max_length=100, description="디바이스 이름")
    location: str = Field(..., max_length=100, description="설치 위치 (예: 거실, 주방)")
    mqtt_topic: str = Field(..., max_length=200, description="MQTT 토픽")


class DeviceCreate(DeviceBase):
    """디바이스 생성 요청 스키마"""
    pass


class DeviceUpdate(BaseModel):
    """디바이스 수정 요청 스키마 (모든 필드 선택적)"""
    name: Optional[str] = Field(None, max_length=100, description="디바이스 이름")
    location: Optional[str] = Field(None, max_length=100, description="설치 위치")
    mqtt_topic: Optional[str] = Field(None, max_length=200, description="MQTT 토픽")


class DeviceResponse(DeviceBase):
    """디바이스 응답 스키마"""
    id: int
    is_active: bool = Field(description="콘센트 On/Off 상태")
    current_power: float = Field(description="현재 전력(W)")
    temperature: float = Field(description="내부 온도(°C)")
    is_online: bool = Field(description="디바이스 연결 상태")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceStatus(BaseModel):
    """디바이스 실시간 상태 스키마"""
    id: int
    name: str
    is_active: bool = Field(description="콘센트 On/Off 상태")
    current_power: float = Field(description="현재 전력(W)")
    temperature: float = Field(description="내부 온도(°C)")
    is_online: bool = Field(description="디바이스 연결 상태")

    model_config = {"from_attributes": True}
