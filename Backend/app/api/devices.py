"""
디바이스 센서 데이터 API 라우터
MQTT에서 파싱된 디바이스 센서 데이터를 조회하는 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.device import DeviceListResponse, DeviceResponse
from app.services.device_service import DeviceService

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
