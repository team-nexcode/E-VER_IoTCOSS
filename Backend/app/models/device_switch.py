"""
디바이스 스위치 상태 모델
전원 제어 명령 상태를 저장합니다.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DeviceSwitch(Base):
    """디바이스 스위치 제어 상태 모델"""
    __tablename__ = "device_switch"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_mac: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="MAC 주소"
    )
    desired_state: Mapped[str] = mapped_column(
        String(10), nullable=False, default="off", comment="제어 명령 상태 (on/off)"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="마지막 업데이트 시각"
    )

    def __repr__(self) -> str:
        return f"<DeviceSwitch(mac='{self.device_mac}', state='{self.desired_state}')>"
