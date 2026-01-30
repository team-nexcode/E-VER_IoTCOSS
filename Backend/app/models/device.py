"""
디바이스(스마트 콘센트) 모델
IoT 디바이스의 정보와 상태를 저장합니다.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Device(Base):
    """스마트 콘센트 디바이스 모델"""
    __tablename__ = "devices"

    # 기본 키
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 디바이스 기본 정보
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="디바이스 이름")
    location: Mapped[str] = mapped_column(String(100), nullable=False, comment="설치 위치 (예: 거실, 주방)")
    mqtt_topic: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, comment="MQTT 토픽")

    # 디바이스 상태 정보
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, comment="콘센트 On/Off 상태")
    current_power: Mapped[float] = mapped_column(Float, default=0.0, comment="현재 전력(W)")
    temperature: Mapped[float] = mapped_column(Float, default=0.0, comment="내부 온도(°C)")
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, comment="디바이스 연결 상태")

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="생성 시각"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정 시각"
    )

    # 전력 로그 관계 (1:N)
    power_logs = relationship("PowerLog", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, name='{self.name}', location='{self.location}', active={self.is_active})>"
