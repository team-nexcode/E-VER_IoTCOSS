"""
스케줄 실행 서비스
등록된 스케줄을 주기적으로 확인하고 시간이 되면 자동으로 전원 제어
"""

import asyncio
import json
import logging
from datetime import datetime, time as dt_time, timezone, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.schedule import Schedule
from app.models.device_switch import DeviceSwitch
from app.models.system_log import SystemLog
from app.services.mobius_service import MobiusService

logger = logging.getLogger(__name__)

# 한국 시간대 (KST = UTC+9)
KST = timezone(timedelta(hours=9))


def get_naive_kst_now():
    """timezone-naive KST 시간 반환 (DB 저장용)"""
    kst_time = datetime.now(KST)
    return datetime(kst_time.year, kst_time.month, kst_time.day,
                   kst_time.hour, kst_time.minute, kst_time.second, kst_time.microsecond)


class ScheduleService:
    """스케줄 실행 서비스"""
    
    def __init__(self):
        self.mobius_service = MobiusService()
        self.is_running = False
        self.last_checked_minute = -1
    
    async def start(self):
        """스케줄 서비스 시작"""
        print("=" * 80)
        print("[SCHEDULE SERVICE] START() 함수 진입!")
        print("=" * 80)
        
        if self.is_running:
            logger.warning("스케줄 서비스가 이미 실행 중입니다.")
            print("[SCHEDULE SERVICE] 이미 실행 중")
            return
        
        self.is_running = True
        logger.info("=" * 50)
        logger.info("스케줄 서비스 시작 - 1분마다 스케줄 체크")
        logger.info("=" * 50)
        
        print("[SCHEDULE SERVICE] is_running = True 설정 완료")
        
        # 서비스 시작 로그를 DB에 기록
        try:
            print("[SCHEDULE SERVICE] SystemLog DB 저장 시도...")
            async with get_db_session() as db:
                start_log = SystemLog(
                    timestamp=get_naive_kst_now(),
                    type="SYSTEM",
                    level="info",
                    source="Schedule",
                    message="스케줄 서비스 시작됨",
                    detail=None
                )
                db.add(start_log)
                await db.commit()
            print("[SCHEDULE SERVICE] SystemLog DB 저장 성공!")
        except Exception as e:
            logger.error(f"스케줄 서비스 시작 로그 실패: {e}")
            print(f"[SCHEDULE SERVICE] SystemLog DB 저장 실패: {e}")
        
        print("[SCHEDULE SERVICE] while 루프 시작...")

        
        while self.is_running:
            try:
                await self._check_schedules()
                await asyncio.sleep(60)  # 1분마다 체크
            except Exception as e:
                logger.error(f"스케줄 체크 중 오류: {e}", exc_info=True)
                # 오류를 SystemLog에 기록 (새 세션 사용)
                try:
                    async with get_db_session() as db:
                        error_log = SystemLog(
                            timestamp=get_naive_kst_now(),
                            type="SYSTEM",
                            level="error",
                            source="Schedule",
                            message=f"스케줄 체크 중 오류: {str(e)}",
                            detail=None
                        )
                        db.add(error_log)
                        await db.commit()
                except Exception as log_error:
                    logger.error(f"오류 로그 저장 실패: {log_error}")
                await asyncio.sleep(60)  # 에러 발생 시에도 1분 후 재시도
    
    async def stop(self):
        """스케줄 서비스 중지"""
        self.is_running = False
        logger.info("스케줄 서비스 중지")
    
    async def _check_schedules(self):
        """현재 시간에 실행할 스케줄 확인 및 실행"""
        now = datetime.now(KST)  # 한국 시간 사용
        current_time = now.time().replace(second=0, microsecond=0)
        current_day = now.weekday()  # 0=월요일, 6=일요일
        current_minute = now.hour * 60 + now.minute
        
        # 같은 분에 중복 실행 방지
        if current_minute == self.last_checked_minute:
            # 30초마다 체크 시도는 하지만 같은 분은 스킵
            async with get_db_session() as db:
                skip_log = SystemLog(
                    timestamp=get_naive_kst_now(),
                    type="SYSTEM",
                    level="info",
                    source="Schedule",
                    message=f"30초 체크: {now.strftime('%H:%M:%S')} (같은 분이라 스킵)",
                    detail=None
                )
                db.add(skip_log)
                await db.commit()
            return
        
        self.last_checked_minute = current_minute
        
        logger.debug(f"[스케줄 체크] 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S %Z')} (요일: {current_day})")
        
        async with get_db_session() as db:
            # 활성화된 스케줄 조회
            result = await db.execute(
                select(Schedule).where(Schedule.enabled == True)
            )
            schedules: List[Schedule] = result.scalars().all()
            
            logger.info(f"[스케줄 체크] 활성 스케줄 {len(schedules)}개 발견")
            
            # System Log에 체크 기록
            check_log = SystemLog(
                timestamp=get_naive_kst_now(),
                type="SYSTEM",
                level="info",
                source="Schedule",
                message=f"스케줄 체크: {now.strftime('%H:%M:%S')} | 활성 스케줄 {len(schedules)}개",
                detail=None
            )
            db.add(check_log)
            await db.commit()
            
            for schedule in schedules:
                # 요일 확인
                days = [int(d.strip()) for d in schedule.days_of_week.split(',')]
                logger.debug(f"[스케줄] {schedule.schedule_name} - 실행 요일: {days}, 현재 요일: {current_day}")
                
                if current_day not in days:
                    logger.debug(f"[스케줄] {schedule.schedule_name} - 오늘은 실행 안 함 (요일 불일치)")
                    continue
                
                # 시간을 time 객체로 변환
                if isinstance(schedule.start_time, dt_time):
                    start_time_original = schedule.start_time
                    start_time = schedule.start_time.replace(second=0, microsecond=0)
                else:
                    start_time_original = dt_time.fromisoformat(str(schedule.start_time))
                    start_time = start_time_original.replace(second=0, microsecond=0)
                
                if isinstance(schedule.end_time, dt_time):
                    end_time_original = schedule.end_time
                    end_time = schedule.end_time.replace(second=0, microsecond=0)
                else:
                    end_time_original = dt_time.fromisoformat(str(schedule.end_time))
                    end_time = end_time_original.replace(second=0, microsecond=0)
                
                logger.info(f"[스케줄 비교] {schedule.schedule_name}")
                logger.info(f"  - 현재: {current_time} / 시작: {start_time} / 종료: {end_time}")
                
                # System Log에 스케줄 비교 기록
                detail_info = {
                    "schedule_name": schedule.schedule_name,
                    "current": str(current_time),
                    "start": str(start_time),
                    "end": str(end_time),
                    "start_original": str(start_time_original),
                    "end_original": str(end_time_original)
                }
                comparison_log = SystemLog(
                    timestamp=get_naive_kst_now(),
                    type="SYSTEM",
                    level="info",
                    source="Schedule",
                    message=f"비교: {schedule.schedule_name} | 현재={current_time} 시작={start_time} 종료={end_time}",
                    detail=json.dumps(detail_info, ensure_ascii=False)
                )
                db.add(comparison_log)
                await db.commit()
                
                # start_time이 00:00:00이 아닐 때만 체크 (ON 스케줄)
                if start_time_original != dt_time(0, 0, 0) and current_time == start_time:
                    logger.info(f"스케줄 실행 (ON): {schedule.schedule_name} (MAC: {schedule.device_mac})")
                    
                    exec_log = SystemLog(
                        timestamp=get_naive_kst_now(),
                        type="SYSTEM",
                        level="info",
                        source="Schedule",
                        message=f"ON 실행: {schedule.schedule_name} ({schedule.device_mac})",
                        detail=json.dumps({"mac": schedule.device_mac, "action": "on"}, ensure_ascii=False)
                    )
                    db.add(exec_log)
                    await db.commit()
                    
                    await self._execute_power_control(schedule.device_mac, "on")
                
                # end_time이 23:59:59가 아닐 때만 체크 (OFF 스케줄)
                elif end_time_original != dt_time(23, 59, 59) and current_time == end_time:
                    logger.info(f"스케줄 실행 (OFF): {schedule.schedule_name} (MAC: {schedule.device_mac})")
                    
                    exec_log = SystemLog(
                        timestamp=get_naive_kst_now(),
                        type="SYSTEM",
                        level="info",
                        source="Schedule",
                        message=f"OFF 실행: {schedule.schedule_name} ({schedule.device_mac})",
                        detail=json.dumps({"mac": schedule.device_mac, "action": "off"}, ensure_ascii=False)
                    )
                    db.add(exec_log)
                    await db.commit()
                    
                    await self._execute_power_control(schedule.device_mac, "off")
    
    async def _execute_power_control(self, device_mac: str, power_state: str):
        """전원 제어 실행 - 기존 API 재사용"""
        try:
            logger.info(f"[전원 제어 시작] MAC: {device_mac}, 상태: {power_state}")
            
            # 기존 전원 제어 API를 직접 호출
            from app.api.devices import control_device_power
            from app.schemas.device import PowerControlRequest
            
            async with get_db_session() as db:
                request = PowerControlRequest(
                    mac_address=device_mac,
                    power_state=power_state
                )
                
                response = await control_device_power(request, db)
                
                logger.info(f"전원 제어 완료: {response}")
                
                # SystemLog에 성공 기록
                success_log = SystemLog(
                    timestamp=get_naive_kst_now(),
                    type="SYSTEM",
                    level="info",
                    source="Schedule",
                    message=f"전원 제어 성공: {device_mac} → {power_state}",
                    detail=f"Mobius 응답: {response.mobius_status}"
                )
                db.add(success_log)
                await db.commit()
        
        except Exception as e:
            logger.error(f"스케줄 전원 제어 중 오류: {e}", exc_info=True)
            # 오류도 SystemLog에 기록
            try:
                async with get_db_session() as db:
                    error_log = SystemLog(
                        timestamp=get_naive_kst_now(),
                        type="SYSTEM",
                        level="error",
                        source="Schedule",
                        message=f"전원 제어 오류: {device_mac} → {power_state}",
                        detail=str(e)
                    )
                    db.add(error_log)
                    await db.commit()
            except Exception as log_error:
                logger.error(f"오류 로그 저장 실패: {log_error}")


# 전역 스케줄 서비스 인스턴스
schedule_service = ScheduleService()
