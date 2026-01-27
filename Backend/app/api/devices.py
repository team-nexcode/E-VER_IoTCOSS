"""
디바이스 API 라우터
스마트 콘센트 디바이스의 CRUD 및 제어 엔드포인트를 제공합니다.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceStatus, DeviceUpdate
from app.services.device_service import DeviceService

router = APIRouter(prefix="/api/devices", tags=["디바이스"])


@router.get("/", response_model=List[DeviceResponse], summary="전체 디바이스 목록 조회")
async def get_devices(db: AsyncSession = Depends(get_db)):
    """등록된 모든 디바이스 목록을 반환합니다."""
    service = DeviceService(db)
    devices = await service.get_all_devices()
    return devices


@router.get("/{device_id}", response_model=DeviceResponse, summary="개별 디바이스 상세 조회")
async def get_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """특정 디바이스의 상세 정보를 반환합니다."""
    service = DeviceService(db)
    device = await service.get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"디바이스(ID: {device_id})를 찾을 수 없습니다."
        )
    return device


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED, summary="디바이스 등록")
async def create_device(device_data: DeviceCreate, db: AsyncSession = Depends(get_db)):
    """새로운 디바이스를 등록합니다."""
    service = DeviceService(db)
    device = await service.create_device(device_data)
    return device


@router.put("/{device_id}", response_model=DeviceResponse, summary="디바이스 수정")
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """디바이스 정보를 수정합니다."""
    service = DeviceService(db)
    device = await service.update_device(device_id, device_data)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"디바이스(ID: {device_id})를 찾을 수 없습니다."
        )
    return device


@router.post("/{device_id}/toggle", response_model=DeviceResponse, summary="디바이스 On/Off 토글")
async def toggle_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """디바이스의 전원 상태를 토글합니다 (On ↔ Off)."""
    service = DeviceService(db)
    device = await service.toggle_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"디바이스(ID: {device_id})를 찾을 수 없습니다."
        )
    return device


@router.get("/{device_id}/status", response_model=DeviceStatus, summary="디바이스 실시간 상태 조회")
async def get_device_status(device_id: int, db: AsyncSession = Depends(get_db)):
    """디바이스의 실시간 상태를 반환합니다."""
    service = DeviceService(db)
    device = await service.get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"디바이스(ID: {device_id})를 찾을 수 없습니다."
        )
    return device
