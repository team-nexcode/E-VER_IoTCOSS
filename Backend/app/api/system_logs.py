"""
시스템 로그 라우터
MQTT 및 시스템 이벤트 로그를 조회/삭제하는 엔드포인트를 제공합니다.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.system_log import SystemLog
from app.schemas.system_log import SystemLogListResponse, SystemLogResponse

router = APIRouter(prefix="/api/system-logs", tags=["시스템 로그"])


@router.get("/", response_model=SystemLogListResponse, summary="시스템 로그 목록 조회")
async def get_system_logs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    type: Optional[str] = Query(None, description="로그 타입 필터 (CONNECTION, MESSAGE, ERROR, SYSTEM)"),
    search: Optional[str] = Query(None, description="메시지 검색어"),
    db: AsyncSession = Depends(get_db),
):
    """시스템 로그를 페이지네이션과 필터를 적용하여 조회합니다."""
    query = select(SystemLog)
    count_query = select(func.count(SystemLog.id))

    if type:
        query = query.where(SystemLog.type == type.upper())
        count_query = count_query.where(SystemLog.type == type.upper())
    if search:
        query = query.where(SystemLog.message.ilike(f"%{search}%"))
        count_query = count_query.where(SystemLog.message.ilike(f"%{search}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * size
    query = query.order_by(desc(SystemLog.timestamp)).offset(offset).limit(size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return SystemLogListResponse(
        items=[SystemLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        size=size,
    )


@router.delete("/", summary="시스템 로그 전체 삭제")
async def delete_all_system_logs(db: AsyncSession = Depends(get_db)):
    """모든 시스템 로그를 삭제합니다."""
    await db.execute(delete(SystemLog))
    return {"message": "모든 시스템 로그가 삭제되었습니다."}
