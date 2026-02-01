"""
디바이스 센서 데이터 Pydantic 스키마
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class PowerControlRequest(BaseModel):
    """디바이스 전원 제어 요청 스키마"""
    mac_address: str = Field(..., description="제어할 디바이스 MAC 주소")
    power_state: str = Field(..., description="전원 상태 (on/off)")
    
    @field_validator("power_state")
    @classmethod
    def validate_power_state(cls, v: str) -> str:
        v = v.lower()
        if v not in ["on", "off"]:
            raise ValueError("power_state는 'on' 또는 'off'만 가능합니다")
        return v


class PowerControlResponse(BaseModel):
    """전원 제어 응답 스키마"""
    success: bool
    message: str
    controlled_devices: int = Field(0, description="제어된 디바이스 수")
    device_list: List[str] = Field(default_factory=list, description="제어된 디바이스 MAC 목록")
    mobius_response: Optional[dict] = None
