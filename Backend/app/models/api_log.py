"""
API 로그 모델
Mobius 서버와의 모든 HTTP 통신 로그를 저장합니다.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ApiLog(Base):
    """API 통신 로그 모델"""
    __tablename__ = "api_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="요청 시각"
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False, comment="HTTP 메서드")
    url: Mapped[str] = mapped_column(String(500), nullable=False, comment="요청 URL")
    request_headers: Mapped[str | None] = mapped_column(Text, nullable=True, comment="요청 헤더 (JSON)")
    request_body: Mapped[str | None] = mapped_column(Text, nullable=True, comment="요청 바디 (JSON)")
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="응답 상태 코드")
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True, comment="응답 바디 (JSON)")
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True, comment="소요 시간 (ms)")
    direction: Mapped[str] = mapped_column(
        String(10), default="outbound", nullable=False, comment="통신 방향 (outbound/inbound)"
    )

    def __repr__(self) -> str:
        return f"<ApiLog(id={self.id}, method='{self.method}', url='{self.url}', status={self.response_status})>"
