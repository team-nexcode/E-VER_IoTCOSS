"""
스케줄 관리 API 라우터
디바이스 전원 제어 스케줄 등록, 조회, 수정, 삭제
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schedule import Schedule
from app.models.device_mac import DeviceMac
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse

router = APIRouter(prefix="/api/schedules", tags=["schedules"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ScheduleResponse, summary="스케줄 생성")
async def create_schedule(
    schedule: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    새 스케줄을 생성합니다.
    - device_mac: 제어할 디바이스 MAC 주소
    - start_time: 전원 ON 시간
    - end_time: 전원 OFF 시간
    - days_of_week: 실행 요일 (0=월~6=일, 예: "0,2,4" = 월수금)
    """
    try:
        # 디바이스 존재 확인
        result = await db.execute(
            select(DeviceMac).where(DeviceMac.device_mac == schedule.device_mac)
        )
        device = result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=404, detail="디바이스를 찾을 수 없습니다.")
        
        # 스케줄 생성
        new_schedule = Schedule(**schedule.model_dump())
        db.add(new_schedule)
        await db.commit()
        await db.refresh(new_schedule)
        
        logger.info(f"스케줄 생성: {new_schedule.schedule_name} (MAC: {schedule.device_mac})")
        return new_schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 생성 중 오류: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"스케줄 생성 실패: {str(e)}")


@router.get("", response_model=List[ScheduleResponse], summary="전체 스케줄 조회")
async def get_schedules(
    device_mac: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    등록된 스케줄 목록을 조회합니다.
    - device_mac: 특정 디바이스의 스케줄만 조회 (선택)
    """
    try:
        query = select(Schedule)
        if device_mac:
            query = query.where(Schedule.device_mac == device_mac)
        
        result = await db.execute(query.order_by(Schedule.start_time))
        schedules = result.scalars().all()
        return schedules
        
    except Exception as e:
        logger.error(f"스케줄 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"스케줄 조회 실패: {str(e)}")


@router.get("/{schedule_id}", response_model=ScheduleResponse, summary="스케줄 상세 조회")
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """특정 스케줄의 상세 정보를 조회합니다."""
    try:
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다.")
        
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"스케줄 조회 실패: {str(e)}")


@router.patch("/{schedule_id}", response_model=ScheduleResponse, summary="스케줄 수정")
async def update_schedule(
    schedule_id: int,
    schedule_update: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """스케줄 정보를 수정합니다."""
    try:
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다.")
        
        # 변경된 필드만 업데이트
        update_data = schedule_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)
        
        await db.commit()
        await db.refresh(schedule)
        
        logger.info(f"스케줄 수정: ID={schedule_id}")
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 수정 중 오류: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"스케줄 수정 실패: {str(e)}")


@router.delete("/{schedule_id}", summary="스케줄 삭제")
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """스케줄을 삭제합니다."""
    try:
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다.")
        
        await db.execute(
            delete(Schedule).where(Schedule.id == schedule_id)
        )
        await db.commit()
        
        logger.info(f"스케줄 삭제: ID={schedule_id}")
        return {"success": True, "message": "스케줄이 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 삭제 중 오류: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"스케줄 삭제 실패: {str(e)}")
