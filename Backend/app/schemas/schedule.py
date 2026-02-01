"""
스케줄 Pydantic 스키마
"""

from datetime import time
from pydantic import BaseModel, Field
from typing import Optional


class ScheduleBase(BaseModel):
    """스케줄 기본 스키마"""
    device_mac: str = Field(..., description="디바이스 MAC 주소")
    schedule_name: str = Field(..., description="스케줄 이름")
    start_time: time = Field(..., description="시작 시간")
    end_time: time = Field(..., description="종료 시간")
    enabled: bool = Field(True, description="스케줄 활성화 여부")
    days_of_week: str = Field("0,1,2,3,4,5,6", description="요일 (0=월~6=일, 쉼표로 구분)")


class ScheduleCreate(ScheduleBase):
    """스케줄 생성 요청"""
    pass


class ScheduleUpdate(BaseModel):
    """스케줄 수정 요청"""
    schedule_name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    enabled: Optional[bool] = None
    days_of_week: Optional[str] = None


class ScheduleResponse(ScheduleBase):
    """스케줄 응답"""
    id: int
    
    class Config:
        from_attributes = True
