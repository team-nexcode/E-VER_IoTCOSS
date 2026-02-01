"""
시스템 로그 모델
MQTT 메시지 및 시스템 이벤트 로그를 저장합니다.
"""

from datetime import datetime, timezone, timedelta

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# 한국 시간대 (KST = UTC+9)
KST = timezone(timedelta(hours=9))


def get_kst_now():
    """KST 시간을 timezone-naive로 반환"""
    kst_time = datetime.now(KST)
    # timezone 정보를 완전히 제거
    return datetime(kst_time.year, kst_time.month, kst_time.day,
                   kst_time.hour, kst_time.minute, kst_time.second, kst_time.microsecond)


class SystemLog(Base):
    """시스템 로그 모델"""
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=get_kst_now, nullable=False, comment="로그 시각 (KST)"
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="로그 타입 (CONNECTION, MESSAGE, ERROR, SYSTEM)"
    )
    level: Mapped[str] = mapped_column(
        String(10), nullable=False, default="info", comment="로그 레벨 (info, warn, error)"
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="소스 (MQTT, Server, App)"
    )
    message: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="한 줄 요약"
    )
    detail: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON 상세 정보"
    )

    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, type='{self.type}', message='{self.message[:30]}')>"
