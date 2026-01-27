"""
전력 데이터 Pydantic 스키마
전력 사용량 로그의 요청/응답 데이터를 정의합니다.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PowerLogBase(BaseModel):
    """전력 로그 기본 스키마"""
    power_watts: float = Field(..., ge=0, description="전력(W)")
    voltage: float = Field(..., ge=0, description="전압(V)")
    current_amps: float = Field(..., ge=0, description="전류(A)")
    temperature: float = Field(default=0.0, description="온도(°C)")


class PowerLogCreate(PowerLogBase):
    """전력 로그 생성 요청 스키마"""
    device_id: int = Field(..., description="디바이스 ID")


class PowerLogResponse(PowerLogBase):
    """전력 로그 응답 스키마"""
    id: int
    device_id: int
    recorded_at: datetime

    model_config = {"from_attributes": True}


class PowerSummary(BaseModel):
    """전체 전력 요약 스키마"""
    total_devices: int = Field(description="전체 디바이스 수")
    active_devices: int = Field(description="활성 디바이스 수")
    total_power_watts: float = Field(description="총 소비 전력(W)")
    average_power_watts: float = Field(description="평균 소비 전력(W)")
    max_power_watts: float = Field(description="최대 소비 전력(W)")
    total_energy_kwh: Optional[float] = Field(default=None, description="총 에너지 사용량(kWh)")
