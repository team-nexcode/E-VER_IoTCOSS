"""
전력 로그 모델
디바이스의 전력 사용량 이력을 저장합니다.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PowerLog(Base):
    """전력 사용량 로그 모델"""
    __tablename__ = "power_logs"

    # 기본 키
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 디바이스 외래 키
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, comment="디바이스 ID"
    )

    # 전력 측정 데이터
    power_watts: Mapped[float] = mapped_column(Float, nullable=False, comment="전력(W)")
    voltage: Mapped[float] = mapped_column(Float, nullable=False, comment="전압(V)")
    current_amps: Mapped[float] = mapped_column(Float, nullable=False, comment="전류(A)")
    temperature: Mapped[float] = mapped_column(Float, default=0.0, comment="온도(°C)")

    # 기록 시각
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="측정 시각"
    )

    # 디바이스 관계 (N:1)
    device = relationship("Device", back_populates="power_logs")

    def __repr__(self) -> str:
        return f"<PowerLog(id={self.id}, device_id={self.device_id}, power={self.power_watts}W)>"
