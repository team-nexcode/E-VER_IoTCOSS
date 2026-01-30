"""
전력 데이터 API 라우터
디바이스 전력 사용량 조회 및 요약 정보를 제공합니다.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device import Device
from app.models.power_log import PowerLog
from app.schemas.power import PowerLogResponse, PowerSummary

router = APIRouter(prefix="/api/power", tags=["전력 데이터"])


@router.get("/{device_id}/current", response_model=Optional[PowerLogResponse], summary="현재 전력 조회")
async def get_current_power(device_id: int, db: AsyncSession = Depends(get_db)):
    """특정 디바이스의 현재(최신) 전력 데이터를 반환합니다."""
    # 디바이스 존재 여부 확인
    device_result = await db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"디바이스(ID: {device_id})를 찾을 수 없습니다."
        )

    # 최신 전력 로그 조회
    result = await db.execute(
        select(PowerLog)
        .where(PowerLog.device_id == device_id)
        .order_by(PowerLog.recorded_at.desc())
        .limit(1)
    )
    power_log = result.scalar_one_or_none()
    return power_log


@router.get("/{device_id}/history", response_model=List[PowerLogResponse], summary="전력 이력 조회")
async def get_power_history(
    device_id: int,
    hours: int = Query(default=24, ge=1, le=720, description="조회할 시간 범위 (기본: 24시간)"),
    limit: int = Query(default=100, ge=1, le=1000, description="최대 결과 수"),
    db: AsyncSession = Depends(get_db),
):
    """특정 디바이스의 전력 사용 이력을 반환합니다."""
    # 디바이스 존재 여부 확인
    device_result = await db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"디바이스(ID: {device_id})를 찾을 수 없습니다."
        )

    # 지정된 시간 범위 내 전력 로그 조회
    since = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        select(PowerLog)
        .where(PowerLog.device_id == device_id, PowerLog.recorded_at >= since)
        .order_by(PowerLog.recorded_at.desc())
        .limit(limit)
    )
    power_logs = result.scalars().all()
    return power_logs


@router.get("/summary", response_model=PowerSummary, summary="전체 전력 요약 조회")
async def get_power_summary(db: AsyncSession = Depends(get_db)):
    """전체 디바이스의 전력 사용 요약 정보를 반환합니다."""
    # 전체 디바이스 수 조회
    total_result = await db.execute(select(func.count(Device.id)))
    total_devices = total_result.scalar() or 0

    # 활성(On) 디바이스 수 조회
    active_result = await db.execute(
        select(func.count(Device.id)).where(Device.is_active == True)
    )
    active_devices = active_result.scalar() or 0

    # 전력 통계 계산
    power_stats = await db.execute(
        select(
            func.coalesce(func.sum(Device.current_power), 0.0),
            func.coalesce(func.avg(Device.current_power), 0.0),
            func.coalesce(func.max(Device.current_power), 0.0),
        ).where(Device.is_active == True)
    )
    stats = power_stats.one()

    return PowerSummary(
        total_devices=total_devices,
        active_devices=active_devices,
        total_power_watts=round(float(stats[0]), 2),
        average_power_watts=round(float(stats[1]), 2),
        max_power_watts=round(float(stats[2]), 2),
    )
