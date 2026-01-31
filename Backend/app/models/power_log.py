"""
전력 로그 모델
디바이스의 전력 사용량 이력을 저장합니다.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PowerLog(Base):
    """전력 사용량 로그 모델"""
    __tablename__ = "power_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="디바이스 ID"
    )
    power_watts: Mapped[float] = mapped_column(Float, nullable=False, comment="전력(W)")
    voltage: Mapped[float] = mapped_column(Float, nullable=False, comment="전압(V)")
    current_amps: Mapped[float] = mapped_column(Float, nullable=False, comment="전류(A)")
    temperature: Mapped[float] = mapped_column(Float, default=0.0, comment="온도(°C)")
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="측정 시각"
    )

    def __repr__(self) -> str:
        return f"<PowerLog(id={self.id}, device_id={self.device_id}, power={self.power_watts}W)>"
