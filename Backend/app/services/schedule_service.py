"""
스케줄 실행 서비스
등록된 스케줄을 주기적으로 확인하고 시간이 되면 자동으로 전원 제어
"""

import asyncio
import logging
from datetime import datetime, time as dt_time
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.schedule import Schedule
from app.models.device_switch import DeviceSwitch
from app.services.mobius_service import MobiusService

logger = logging.getLogger(__name__)


class ScheduleService:
    """스케줄 실행 서비스"""
    
    def __init__(self):
        self.mobius_service = MobiusService()
        self.is_running = False
        self.last_checked_minute = -1
    
    async def start(self):
        """스케줄 서비스 시작"""
        if self.is_running:
            logger.warning("스케줄 서비스가 이미 실행 중입니다.")
            return
        
        self.is_running = True
        logger.info("스케줄 서비스 시작")
        
        while self.is_running:
            try:
                await self._check_schedules()
                await asyncio.sleep(30)  # 30초마다 체크
            except Exception as e:
                logger.error(f"스케줄 체크 중 오류: {e}")
                await asyncio.sleep(30)
    
    async def stop(self):
        """스케줄 서비스 중지"""
        self.is_running = False
        logger.info("스케줄 서비스 중지")
    
    async def _check_schedules(self):
        """현재 시간에 실행할 스케줄 확인 및 실행"""
        now = datetime.now()
        current_time = now.time().replace(second=0, microsecond=0)
        current_day = now.weekday()  # 0=월요일, 6=일요일
        current_minute = now.hour * 60 + now.minute
        
        # 같은 분에 중복 실행 방지
        if current_minute == self.last_checked_minute:
            return
        
        self.last_checked_minute = current_minute
        
        async with get_db_session() as db:
            # 활성화된 스케줄 조회
            result = await db.execute(
                select(Schedule).where(Schedule.enabled == True)
            )
            schedules: List[Schedule] = result.scalars().all()
            
            for schedule in schedules:
                # 요일 확인
                days = [int(d.strip()) for d in schedule.days_of_week.split(',')]
                if current_day not in days:
                    continue
                
                # 시작 시간 체크
                start_time = schedule.start_time.replace(second=0, microsecond=0) if isinstance(schedule.start_time, dt_time) else schedule.start_time
                end_time = schedule.end_time.replace(second=0, microsecond=0) if isinstance(schedule.end_time, dt_time) else schedule.end_time
                
                if current_time == start_time:
                    logger.info(f"스케줄 실행 (ON): {schedule.schedule_name} (MAC: {schedule.device_mac})")
                    await self._execute_power_control(schedule.device_mac, "on", db)
                
                elif current_time == end_time:
                    logger.info(f"스케줄 실행 (OFF): {schedule.schedule_name} (MAC: {schedule.device_mac})")
                    await self._execute_power_control(schedule.device_mac, "off", db)
    
    async def _execute_power_control(self, device_mac: str, power_state: str, db: AsyncSession):
        """전원 제어 실행"""
        try:
            # device_switch 테이블 업데이트
            result = await db.execute(
                select(DeviceSwitch).where(DeviceSwitch.device_mac == device_mac)
            )
            switch = result.scalar_one_or_none()
            
            if switch:
                switch.desired_state = power_state
                switch.updated_at = datetime.utcnow()
            else:
                new_switch = DeviceSwitch(
                    device_mac=device_mac,
                    desired_state=power_state,
                )
                db.add(new_switch)
            
            await db.commit()
            
            # 모든 디바이스의 제어 상태 수집
            result = await db.execute(select(DeviceSwitch))
            all_switches = result.scalars().all()
            
            device_control_map = {s.device_mac: s.desired_state for s in all_switches}
            
            # Mobius로 전송
            payload = {"m2m:cin": {"con": device_control_map}}
            response = await self.mobius_service.create_cin("ae_nexcode", "switch", payload)
            
            if response.get("status") in [200, 201]:
                logger.info(f"스케줄 전원 제어 성공: {device_mac} → {power_state}")
            else:
                logger.error(f"스케줄 전원 제어 실패: {device_mac}, Mobius 응답: {response}")
        
        except Exception as e:
            logger.error(f"스케줄 전원 제어 중 오류: {e}")
            await db.rollback()


# 전역 스케줄 서비스 인스턴스
schedule_service = ScheduleService()
