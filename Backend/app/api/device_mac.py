"""
디바이스 MAC API 라우터
디바이스 MAC 주소의 CRUD 엔드포인트를 제공합니다.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device_mac import DeviceMac
from app.models.system_log import SystemLog
from app.api.websocket import broadcast_system_log, invalidate_device_mac_cache
from app.schemas.device_mac import (
    DeviceMacCreate,
    DeviceMacListResponse,
    DeviceMacResponse,
    DeviceMacUpdate,
)

router = APIRouter(prefix="/api/device_mac", tags=["디바이스 MAC"])


async def _write_system_log(db: AsyncSession, action: str, detail_data: dict):
    """DB 변경 시 시스템 로그를 기록합니다."""
    log_entry = SystemLog(
        type="SYSTEM",
        level="info",
        source="App",
        message=f"[device_mac] {action}: {detail_data.get('device_name', '')} ({detail_data.get('device_mac', '')})",
        detail=json.dumps({"table": "device_mac", "action": action, **detail_data}, ensure_ascii=False),
    )
    db.add(log_entry)


@router.get("/", response_model=DeviceMacListResponse, summary="디바이스 MAC 전체 목록 조회")
async def get_device_macs(db: AsyncSession = Depends(get_db)):
    """등록된 모든 디바이스 MAC 목록을 반환합니다."""
    count_result = await db.execute(select(func.count(DeviceMac.id)))
    total = count_result.scalar() or 0

    result = await db.execute(select(DeviceMac).order_by(DeviceMac.id))
    devices = result.scalars().all()

    return DeviceMacListResponse(
        items=[DeviceMacResponse.model_validate(d) for d in devices],
        total=total,
    )


@router.post("/", response_model=DeviceMacResponse, status_code=status.HTTP_201_CREATED, summary="디바이스 MAC 등록")
async def create_device_mac(data: DeviceMacCreate, db: AsyncSession = Depends(get_db)):
    """새로운 디바이스 MAC을 등록합니다."""
    existing = await db.scalar(
        select(DeviceMac).where(DeviceMac.device_mac == data.device_mac)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"MAC 주소 '{data.device_mac}'는 이미 등록되어 있습니다.",
        )
    device = DeviceMac(
        device_name=data.device_name,
        device_mac=data.device_mac,
        location=data.location,
    )
    db.add(device)
    await db.flush()
    await db.refresh(device)

    detail_data = {
        "device_name": device.device_name,
        "device_mac": device.device_mac,
        "location": device.location,
    }
    await _write_system_log(db, "INSERT", detail_data)
    await db.commit()
    invalidate_device_mac_cache()
    await broadcast_system_log(
        message=f"[device_mac] INSERT: {device.device_name} ({device.device_mac})",
        detail=json.dumps({"table": "device_mac", "action": "INSERT", **detail_data}, ensure_ascii=False),
    )
    return device


@router.put("/{device_id}", response_model=DeviceMacResponse, summary="디바이스 MAC 수정")
async def update_device_mac(
    device_id: int,
    data: DeviceMacUpdate,
    db: AsyncSession = Depends(get_db),
):
    """디바이스 MAC 정보를 수정합니다."""
    device = await db.get(DeviceMac, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"디바이스(ID: {device_id})를 찾을 수 없습니다.",
        )
    old_values = {
        "device_name": device.device_name,
        "device_mac": device.device_mac,
        "location": device.location,
    }
    update_data = data.model_dump(exclude_unset=True)
    if "device_mac" in update_data:
        existing = await db.scalar(
            select(DeviceMac).where(
                DeviceMac.device_mac == update_data["device_mac"],
                DeviceMac.id != device_id,
            )
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"MAC 주소 '{update_data['device_mac']}'는 이미 등록되어 있습니다.",
            )
    for key, value in update_data.items():
        setattr(device, key, value)
    await db.flush()
    await db.refresh(device)

    update_detail = {
        "id": device_id,
        "device_name": device.device_name,
        "device_mac": device.device_mac,
        "location": device.location,
        "old_values": old_values,
    }
    await _write_system_log(db, "UPDATE", update_detail)
    await db.commit()
    invalidate_device_mac_cache()
    await broadcast_system_log(
        message=f"[device_mac] UPDATE: {device.device_name} ({device.device_mac})",
        detail=json.dumps({"table": "device_mac", "action": "UPDATE", **update_detail}, ensure_ascii=False),
    )
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, summary="디바이스 MAC 삭제")
async def delete_device_mac(device_id: int, db: AsyncSession = Depends(get_db)):
    """디바이스 MAC을 삭제합니다."""
    device = await db.get(DeviceMac, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"디바이스(ID: {device_id})를 찾을 수 없습니다.",
        )
    deleted_info = {
        "id": device_id,
        "device_name": device.device_name,
        "device_mac": device.device_mac,
        "location": device.location,
    }
    await db.delete(device)

    await _write_system_log(db, "DELETE", deleted_info)
    await db.commit()
    invalidate_device_mac_cache()
    await broadcast_system_log(
        message=f"[device_mac] DELETE: {deleted_info['device_name']} ({deleted_info['device_mac']})",
        detail=json.dumps({"table": "device_mac", "action": "DELETE", **deleted_info}, ensure_ascii=False),
    )


@router.patch("/{device_id}/ai-control", response_model=DeviceMacResponse, summary="AI 자동 제어 토글")
async def toggle_ai_control(
    device_id: int,
    enabled: bool,
    db: AsyncSession = Depends(get_db),
):
    """디바이스의 AI 자동 제어를 활성화/비활성화합니다."""
    device = await db.get(DeviceMac, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"디바이스(ID: {device_id})를 찾을 수 없습니다.",
        )
    
    old_value = device.ai_auto_control
    device.ai_auto_control = enabled
    await db.flush()
    await db.refresh(device)

    detail_data = {
        "id": device_id,
        "device_name": device.device_name,
        "device_mac": device.device_mac,
        "ai_auto_control": enabled,
        "old_value": old_value,
    }
    await _write_system_log(db, "AI_CONTROL_UPDATE", detail_data)
    await db.commit()
    invalidate_device_mac_cache()
    await broadcast_system_log(
        message=f"[device_mac] AI 자동 제어 {'활성화' if enabled else '비활성화'}: {device.device_name}",
        detail=json.dumps({"table": "device_mac", "action": "AI_CONTROL_UPDATE", **detail_data}, ensure_ascii=False),
    )
    return device


@router.get("/ai-enabled", summary="AI 자동 제어가 활성화된 디바이스 목록")
async def get_ai_enabled_devices(db: AsyncSession = Depends(get_db)):
    """AI 자동 제어가 활성화된 디바이스 목록을 반환합니다."""
    result = await db.execute(
        select(DeviceMac).where(DeviceMac.ai_auto_control == True).order_by(DeviceMac.id)
    )
    devices = result.scalars().all()
    
    return {
        "items": [DeviceMacResponse.model_validate(d) for d in devices],
        "total": len(devices),
    }
