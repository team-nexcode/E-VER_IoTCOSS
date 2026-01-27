"""
사용자 모델
시스템 사용자 정보와 인증 데이터를 저장합니다.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """시스템 사용자 모델"""
    __tablename__ = "users"

    # 기본 키
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 사용자 정보
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, comment="사용자 이름"
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="이메일 주소"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="해시된 비밀번호"
    )

    # 권한 정보
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="관리자 여부"
    )

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="가입 시각"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', admin={self.is_admin})>"
