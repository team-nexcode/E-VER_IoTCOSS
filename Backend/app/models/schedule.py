"""
스케줄 모델
디바이스의 전원을 예약 시간에 자동으로 제어하기 위한 스케줄 정보
"""

from sqlalchemy import Column, Integer, String, Time, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Schedule(Base):
    """스케줄 테이블"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    device_mac = Column(String(50), nullable=False, index=True, comment="디바이스 MAC 주소")
    schedule_name = Column(String(100), nullable=False, comment="스케줄 이름")
    start_time = Column(Time, nullable=False, comment="시작 시간 (HH:MM:SS)")
    end_time = Column(Time, nullable=False, comment="종료 시간 (HH:MM:SS)")
    enabled = Column(Boolean, default=True, nullable=False, comment="스케줄 활성화 여부")
    days_of_week = Column(String(20), nullable=False, default="0,1,2,3,4,5,6", comment="요일 (0=월, 6=일)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
