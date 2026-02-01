"""
디바이스 MAC 주소 관리 모델
디바이스 이름, MAC 주소, 설치 위치를 저장합니다.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DeviceMac(Base):
    """디바이스 MAC 주소 모델"""
    __tablename__ = "device_mac"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="디바이스 이름"
    )
    device_mac: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="MAC 주소"
    )
    location: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="설치 위치"
    )
    desired_state: Mapped[str | None] = mapped_column(
        String(10), nullable=True, default="off", comment="제어 명령 상태 (on/off) - 우리가 보낸 명령"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="등록 시각"
    )

    def __repr__(self) -> str:
        return f"<DeviceMac(id={self.id}, name='{self.device_name}', mac='{self.device_mac}', desired='{self.desired_state}')>"
