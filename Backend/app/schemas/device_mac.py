"""
디바이스 MAC Pydantic 스키마
API 요청/응답 데이터의 유효성 검사 및 직렬화를 담당합니다.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceMacCreate(BaseModel):
    """디바이스 MAC 등록 요청 스키마"""
    device_name: str = Field(..., max_length=100, description="디바이스 이름")
    device_mac: str = Field(..., max_length=50, description="MAC 주소")
    location: str = Field(..., max_length=100, description="설치 위치")


class DeviceMacUpdate(BaseModel):
    """디바이스 MAC 수정 요청 스키마 (모든 필드 선택적)"""
    device_name: Optional[str] = Field(None, max_length=100, description="디바이스 이름")
    device_mac: Optional[str] = Field(None, max_length=50, description="MAC 주소")
    location: Optional[str] = Field(None, max_length=100, description="설치 위치")


class DeviceMacResponse(BaseModel):
    """디바이스 MAC 응답 스키마"""
    id: int
    device_name: str
    device_mac: str
    location: str
    ai_auto_control: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceMacListResponse(BaseModel):
    """디바이스 MAC 목록 응답 스키마"""
    items: List[DeviceMacResponse]
    total: int
