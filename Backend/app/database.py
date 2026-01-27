"""
데이터베이스 연결 및 세션 관리 모듈
SQLAlchemy 비동기 엔진과 세션을 설정합니다.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# 비동기 데이터베이스 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 디버그 모드에서 SQL 쿼리 로깅
    pool_size=20,  # 커넥션 풀 크기
    max_overflow=10,  # 최대 추가 커넥션 수
)

# 비동기 세션 팩토리
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """모든 모델의 기본 클래스"""
    pass


async def get_db() -> AsyncSession:
    """
    FastAPI 의존성 주입용 데이터베이스 세션 제공 함수
    요청이 끝나면 자동으로 세션을 닫습니다.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
