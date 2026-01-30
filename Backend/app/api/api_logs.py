"""
API 로그 라우터
API 통신 로그를 조회하고 관리하는 엔드포인트를 제공합니다.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.api_log import ApiLog
from app.schemas.api_log import ApiLogListResponse, ApiLogResponse

router = APIRouter(prefix="/api/logs", tags=["API 로그"])


@router.get("/", response_model=ApiLogListResponse, summary="API 로그 목록 조회")
async def get_api_logs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    method: Optional[str] = Query(None, description="HTTP 메서드 필터 (GET, POST, PUT, DELETE)"),
    status_code: Optional[int] = Query(None, alias="status", description="응답 상태 코드 필터"),
    search: Optional[str] = Query(None, description="URL 검색어"),
    direction: Optional[str] = Query(None, description="통신 방향 필터 (outbound/inbound)"),
    db: AsyncSession = Depends(get_db),
):
    """API 통신 로그를 페이지네이션과 필터를 적용하여 조회합니다."""
    query = select(ApiLog)
    count_query = select(func.count(ApiLog.id))

    # 필터 적용
    if method:
        query = query.where(ApiLog.method == method.upper())
        count_query = count_query.where(ApiLog.method == method.upper())
    if status_code:
        query = query.where(ApiLog.response_status == status_code)
        count_query = count_query.where(ApiLog.response_status == status_code)
    if search:
        query = query.where(ApiLog.url.ilike(f"%{search}%"))
        count_query = count_query.where(ApiLog.url.ilike(f"%{search}%"))
    if direction:
        query = query.where(ApiLog.direction == direction)
        count_query = count_query.where(ApiLog.direction == direction)

    # 총 개수 조회
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 정렬 및 페이지네이션
    offset = (page - 1) * size
    query = query.order_by(desc(ApiLog.timestamp)).offset(offset).limit(size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return ApiLogListResponse(
        items=[ApiLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{log_id}", response_model=ApiLogResponse, summary="API 로그 상세 조회")
async def get_api_log(log_id: int, db: AsyncSession = Depends(get_db)):
    """특정 API 로그의 상세 정보를 조회합니다."""
    result = await db.execute(select(ApiLog).where(ApiLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API 로그(ID: {log_id})를 찾을 수 없습니다.",
        )
    return ApiLogResponse.model_validate(log)


@router.delete("/", summary="API 로그 전체 삭제")
async def delete_all_logs(db: AsyncSession = Depends(get_db)):
    """모든 API 통신 로그를 삭제합니다."""
    await db.execute(delete(ApiLog))
    return {"message": "모든 API 로그가 삭제되었습니다."}
