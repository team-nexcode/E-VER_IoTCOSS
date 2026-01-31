"""
디바이스 센서 데이터 모델
MQTT 메시지에서 파싱된 디바이스 센서 데이터를 저장합니다.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Device(Base):
    """디바이스 센서 데이터 모델"""
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="디바이스 이름 (device_mac 테이블 매칭)"
    )
    device_mac: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="MAC 주소"
    )
    temperature: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="온도 (con.temp)"
    )
    humidity: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="습도 (con.humi)"
    )
    energy_amp: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="에너지 (con.energy)"
    )
    relay_status: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="릴레이 상태 (on/off)"
    )
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="로그 시각 (ct 파싱)"
    )

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, name='{self.device_name}', mac='{self.device_mac}')>"
