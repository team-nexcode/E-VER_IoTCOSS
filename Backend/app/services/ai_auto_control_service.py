"""
AI 자동 제어 서비스
profiles.json 기반으로 AI가 추천한 대로 릴레이를 자동 제어합니다.
"""

import asyncio
import logging
from typing import List

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.device_mac import DeviceMac
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_ai_enabled_devices(db: AsyncSession) -> List[DeviceMac]:
    """AI 자동 제어가 활성화된 디바이스 목록 조회"""
    result = await db.execute(
        select(DeviceMac).where(DeviceMac.ai_auto_control == True)
    )
    return result.scalars().all()


async def get_ai_recommendation(device_mac: str) -> dict:
    """AI 서버로부터 특정 디바이스의 제어 추천 받기"""
    ai_server_url = settings.AI_REPORT_URL or "http://iotcoss.nexcode.kr:8001"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{ai_server_url}/devices/{device_mac}/auto-control-recommendation"
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"AI 추천 조회 실패 ({device_mac}): {e}")
        return {"action": "off", "reason": f"오류: {e}"}


async def run_ai_auto_control_cycle():
    """AI 자동 제어 1회 실행 사이클"""
    # devices.py의 control_device_power를 사용하기 위해 import
    from app.api.devices import PowerControlRequest, control_device_power
    
    async with async_session() as db:
        try:
            # 1. AI 자동 제어 활성화된 디바이스 조회
            devices = await get_ai_enabled_devices(db)
            
            if not devices:
                logger.debug("[AI_CONTROL] AI 자동 제어가 활성화된 디바이스 없음")
                return
            
            logger.info(f"[AI_CONTROL] 제어 대상: {len(devices)}개 디바이스")
            
            # 2. 각 디바이스별로 AI 추천 받기 및 제어 실행
            for device in devices:
                recommendation = await get_ai_recommendation(device.device_mac)
                action = recommendation.get("action", "off")
                # action이 대소문자 상관없이 들어올 수 있으므로 소문자로 변환
                desired_state = action.lower()
                
                try:
                    # 기존 control_device_power 함수 사용
                    request = PowerControlRequest(
                        mac_address=device.device_mac,
                        power_state=desired_state
                    )
                    await control_device_power(request, db)
                    
                    logger.info(
                        f"[AI_CONTROL] {device.device_name} ({device.device_mac}) → {desired_state} "
                        f"| 사유: {recommendation.get('reason', 'N/A')}"
                    )
                except Exception as e:
                    logger.error(f"[AI_CONTROL] 제어 실패 {device.device_name}: {e}")
                
                await asyncio.sleep(0.5)  # 각 디바이스 사이 0.5초 대기
            
            logger.info("[AI_CONTROL] 사이클 완료")
            
        except Exception as e:
            logger.error(f"[AI_CONTROL] 사이클 실행 중 오류: {e}")


async def start_ai_auto_control_service(interval_seconds: int = 600):
    """
    AI 자동 제어 서비스 시작
    
    Args:
        interval_seconds: 실행 주기 (초 단위, 기본 600초 = 10분)
    """
    logger.info(f"🤖 AI 자동 제어 서비스 시작 (주기: {interval_seconds}초)")
    
    while True:
        try:
            await run_ai_auto_control_cycle()
        except Exception as e:
            logger.error(f"[AI_CONTROL] 서비스 오류: {e}")
        
        # 다음 실행까지 대기
        await asyncio.sleep(interval_seconds)


# 서비스 직접 실행용
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    
    asyncio.run(start_ai_auto_control_service(interval))
