"""
대시보드 월별 전력량/요금 요약 모델
매달 누적 전력량(kWh)과 예상 전기요금(원)을 저장합니다.
"""

from sqlalchemy import Integer, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Dashboard(Base):
    """월별 대시보드 요약 모델"""
    __tablename__ = "dashboard"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_dashboard_year_month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, comment="연도")
    month: Mapped[int] = mapped_column(Integer, nullable=False, comment="월")
    month_totalenergy: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="월 누적 전력량 (kWh)"
    )
    month_energybill: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="예상 전기요금 (원)"
    )

    def __repr__(self) -> str:
        return f"<Dashboard({self.year}-{self.month:02d}: {self.month_totalenergy}kWh, {self.month_energybill}원)>"
