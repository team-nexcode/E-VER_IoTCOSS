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
    """일별 총 전력량(kWh)을 반환합니다. device_mac이 있으면 해당 디바이스만, 없으면 전체 합계를 반환합니다."""
    from app.api.websocket import calculate_energy_kwh
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    result_data = []
    
    # 각 날짜별로 전력량 계산
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%m/%d")
        
        # 디바이스별 또는 전체 전력량 계산
        if device_mac:
            # 특정 디바이스만 계산 - devices 테이블에서 직접 계산
            VOLTAGE = 220.0
            start_dt = datetime.combine(current_date, datetime.min.time())
            end_dt = datetime.combine(current_date + timedelta(days=1), datetime.min.time())
            
            result = await db.execute(
                select(Device.energy_amp, Device.timestamp)
                .where(
                    Device.device_mac == device_mac,
                    Device.timestamp >= start_dt,
                    Device.timestamp < end_dt,
                    Device.energy_amp.isnot(None),
                    Device.timestamp.isnot(None)
                )
                .order_by(Device.timestamp)
            )
            rows = result.all()
            
            total_wh = 0.0
            prev_amp = None
            prev_ts = None
            
            for amp, ts in rows:
                if prev_amp is not None and prev_ts is not None:
                    dt_hours = (ts - prev_ts).total_seconds() / 3600
                    if 0 < dt_hours < 6:
                        total_wh += ((prev_amp + amp) / 2) * VOLTAGE * dt_hours
                prev_amp = amp
                prev_ts = ts
            
            kwh = total_wh / 1000
        else:
            # 전체 전력량 - websocket의 calculate_energy_kwh 함수 사용
            kwh = await calculate_energy_kwh(current_date)
        
        result_data.append({
            "date": date_str,
            "power": round(kwh, 3)
        })
    
    return result_data
