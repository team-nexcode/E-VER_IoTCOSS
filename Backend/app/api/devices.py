"""
디바이스 센서 데이터 API 라우터
MQTT에서 파싱된 디바이스 센서 데이터를 조회하는 엔드포인트를 제공합니다.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device_mac import DeviceMac
from app.models.device_switch import DeviceSwitch
from app.schemas.device import (
    DeviceListResponse,
    DeviceResponse,
    PowerControlRequest,
    PowerControlResponse,
)
from app.services.device_service import DeviceService
from app.services.mobius_service import mobius_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/devices", tags=["디바이스"])


@router.get("/", response_model=DeviceListResponse, summary="디바이스 센서 데이터 목록 조회")
async def get_devices(
    limit: int = Query(100, ge=1, le=500, description="조회 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    db: AsyncSession = Depends(get_db),
):
    """MQTT에서 파싱된 디바이스 센서 데이터 목록을 반환합니다."""
    service = DeviceService(db)
    devices, total = await service.get_all_devices(limit=limit, offset=offset)
    return DeviceListResponse(
        items=[DeviceResponse.model_validate(d) for d in devices],
        total=total,
    )


@router.post("/power/control", response_model=PowerControlResponse, summary="디바이스 전원 제어")
async def control_device_power(
    request: PowerControlRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    특정 디바이스의 전원을 제어합니다.
    단, Mobius에는 제어 대상 디바이스뿐만 아니라 모든 등록된 디바이스의 현재 상태를 함께 전송합니다.
    
    예시: mac1을 off로 변경 시 -> {"mac1": "off", "mac2": "on", "mac3": "on"}
    """
    try:
        # 1. 제어하려는 디바이스가 등록되어 있는지 확인
        target_device = await db.scalar(
            select(DeviceMac).where(DeviceMac.device_mac == request.mac_address)
        )
        if not target_device:
            raise HTTPException(
                status_code=404,
                detail=f"MAC 주소 '{request.mac_address}'는 등록되지 않은 디바이스입니다."
            )
        
        # 2. 모든 등록된 디바이스 조회
        result = await db.execute(select(DeviceMac))
        all_devices = result.scalars().all()
        
        # 3. 각 디바이스의 desired_state 조회 (device_switch 테이블)
        device_control_map = {}
        
        for device in all_devices:
            if device.device_mac == request.mac_address:
                # 제어 대상 디바이스는 요청받은 새 상태로 설정
                device_control_map[device.device_mac] = request.power_state
            else:
                # 나머지 디바이스는 device_switch에서 현재 상태 조회
                switch_state = await db.scalar(
                    select(DeviceSwitch.desired_state)
                    .where(DeviceSwitch.device_mac == device.device_mac)
                )
                device_control_map[device.device_mac] = switch_state if switch_state else "off"
        
        # 4. Mobius switch 컨테이너에 전송할 데이터 구성
        payload = {
            "m2m:cin": {
                "con": device_control_map,
                "lbl": ["smart_plug"]  # 필수: Mobius 권한 확인용 라벨
            }
        }
        
        logger.info(f"디바이스 전원 제어 요청: MAC={request.mac_address}, 상태={request.power_state}")
        logger.debug(f"전체 디바이스 상태 전송: {device_control_map}")
        
        # 5. device_switch 테이블에 제어 명령 상태 저장/업데이트
        existing_switch = await db.scalar(
            select(DeviceSwitch).where(DeviceSwitch.device_mac == request.mac_address)
        )
        
        if existing_switch:
            # 기존 레코드 업데이트
            existing_switch.desired_state = request.power_state
            existing_switch.updated_at = datetime.utcnow()
        else:
            # 새 레코드 생성
            new_switch = DeviceSwitch(
                device_mac=request.mac_address,
                desired_state=request.power_state,
            )
            db.add(new_switch)
        
        await db.commit()
        logger.info(f"제어 명령 상태 저장: {request.mac_address} → desired_state={request.power_state}")
        
        # 6. Mobius에 ContentInstance 생성 (switch 컨테이너에 명령 전송)
        response = await mobius_service.create_cin("ae_nexcode", "switch", payload)
        
        if response.get("status") in [200, 201]:
            return PowerControlResponse(
                success=True,
                message=f"디바이스 {request.mac_address}의 전원을 {request.power_state}로 제어했습니다.",
                controlled_devices=len(all_devices),
                device_list=list(device_control_map.keys()),
                mobius_response=response.get("body")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Mobius 전원 제어 실패: {response.get('body')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"디바이스 전원 제어 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"전원 제어 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/power/status", summary="모든 디바이스의 전원 상태 조회")
async def get_devices_power_status(
    db: AsyncSession = Depends(get_db),
):
    """
    모든 등록된 디바이스의 desired_state(제어 명령)와 실제 relay_status를 반환합니다.
    - desired_state: Frontend 제어 버튼에 사용
    - actual_state: 모니터링/디버깅용 (선택적 표시)
    """
    try:
        # 모든 등록된 디바이스 조회
        result = await db.execute(select(DeviceMac))
        all_devices = result.scalars().all()
        
        from app.models.device import Device
        status_list = []
        
        for device in all_devices:
            # device_switch에서 제어 명령 상태 조회
            switch_state = await db.scalar(
                select(DeviceSwitch.desired_state)
                .where(DeviceSwitch.device_mac == device.device_mac)
            )
            
            # 최신 실제 상태 조회 (선택적 - 디버깅용)
            latest_status_result = await db.execute(
                select(Device.relay_status)
                .where(Device.device_mac == device.device_mac)
                .order_by(Device.id.desc())
                .limit(1)
            )
            actual_status = latest_status_result.scalar()
            
            status_list.append({
                "device_name": device.device_name,
                "device_mac": device.device_mac,
                "location": device.location,
                "desired_state": switch_state or "off",  # 제어용 (Frontend 버튼 상태)
                "actual_state": actual_status,  # 참고용 (실제 아두이노 상태)
            })
        
        return {
            "total": len(status_list),
            "devices": status_list
        }
        
    except Exception as e:
        logger.error(f"디바이스 상태 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"상태 조회 중 오류가 발생했습니다: {str(e)}"
        )
