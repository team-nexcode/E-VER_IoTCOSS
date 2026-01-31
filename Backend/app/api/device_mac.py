"""
디바이스 MAC API 라우터
디바이스 MAC 주소의 CRUD 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device_mac import DeviceMac
from app.schemas.device_mac import (
    DeviceMacCreate,
    DeviceMacListResponse,
    DeviceMacResponse,
    DeviceMacUpdate,
)

router = APIRouter(prefix="/api/device_mac", tags=["디바이스 MAC"])


@router.get("/", response_model=DeviceMacListResponse, summary="디바이스 MAC 전체 목록 조회")
async def get_device_macs(db: AsyncSession = Depends(get_db)):
    """등록된 모든 디바이스 MAC 목록을 반환합니다."""
    import traceback
    try:
        count_result = await db.execute(select(func.count(DeviceMac.id)))
        total = count_result.scalar() or 0

        result = await db.execute(select(DeviceMac).order_by(DeviceMac.id))
        devices = result.scalars().all()

        return DeviceMacListResponse(
            items=[DeviceMacResponse.model_validate(d) for d in devices],
            total=total,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


@router.post("/", response_model=DeviceMacResponse, status_code=status.HTTP_201_CREATED, summary="디바이스 MAC 등록")
async def create_device_mac(data: DeviceMacCreate, db: AsyncSession = Depends(get_db)):
    """새로운 디바이스 MAC을 등록합니다."""
    # 중복 MAC 주소 체크
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
    update_data = data.model_dump(exclude_unset=True)
    # 중복 MAC 주소 체크
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
    await db.delete(device)
