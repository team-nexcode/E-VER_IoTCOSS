"""
전력 데이터 API 라우터
디바이스 전력 사용량 조회 및 요약 정보를 제공합니다.
"""

from datetime import datetime, timedelta, date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.power_log import PowerLog
from app.models.device import Device
from app.schemas.power import PowerLogResponse, PowerSummary

router = APIRouter(prefix="/api/power", tags=["전력 데이터"])


@router.get("/{device_id}/current", response_model=Optional[PowerLogResponse], summary="현재 전력 조회")
async def get_current_power(device_id: int, db: AsyncSession = Depends(get_db)):
    """특정 디바이스의 현재(최신) 전력 데이터를 반환합니다."""
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
    """전체 전력 사용 요약 정보를 반환합니다."""
    return PowerSummary(
        total_devices=0,
        active_devices=0,
        total_power_watts=0.0,
        average_power_watts=0.0,
        max_power_watts=0.0,
    )


@router.get("/daily", summary="일별 총 전력량 조회")
async def get_daily_power(
    days: int = Query(default=7, ge=1, le=30, description="조회할 일수 (기본: 7일)"),
    device_mac: Optional[str] = Query(None, description="특정 디바이스 MAC 주소 (없으면 전체)"),
    db: AsyncSession = Depends(get_db)
):
    """일별 총 전력량을 반환합니다. device_mac이 있으면 해당 디바이스만, 없으면 전체 합계를 반환합니다."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    # 날짜별로 그룹화하여 평균 전력 계산
    query = select(
        cast(Device.timestamp, Date).label('date'),
        func.avg(Device.energy_amp).label('avg_power')
    ).where(
        Device.timestamp >= start_date,
        Device.timestamp <= datetime.combine(end_date, datetime.max.time()),
        Device.energy_amp.isnot(None)
    )
    
    if device_mac:
        query = query.where(Device.device_mac == device_mac)
    
    query = query.group_by(cast(Device.timestamp, Date)).order_by(cast(Device.timestamp, Date))
    
    result = await db.execute(query)
    rows = result.all()
    
    # 결과를 date와 power로 변환
    daily_data = []
    for row in rows:
        daily_data.append({
            "date": row.date.strftime("%m/%d"),
            "power": round(row.avg_power or 0, 2)
        })
    
    # 데이터가 없는 날짜는 0으로 채우기
    date_dict = {item["date"]: item["power"] for item in daily_data}
    result_data = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%m/%d")
        result_data.append({
            "date": date_str,
            "power": date_dict.get(date_str, 0)
        })
    
    return result_data
