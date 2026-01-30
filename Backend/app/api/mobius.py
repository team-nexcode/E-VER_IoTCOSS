"""
Mobius 프록시 API 라우터
프론트엔드에서 Mobius 서버 작업을 트리거하는 프록시 엔드포인트를 제공합니다.
"""

from typing import Any, Optional

from fastapi import APIRouter, Body

from app.services.mobius_service import mobius_service

router = APIRouter(prefix="/api/mobius", tags=["Mobius"])


# ==================== CSE ====================
@router.get("/cse", summary="CSE 정보 조회")
async def get_cse():
    """Mobius CSE 기본 정보를 조회합니다."""
    return await mobius_service.get_cse()


# ==================== AE ====================
@router.get("/ae/{ae}", summary="AE 조회")
async def get_ae(ae: str):
    """Application Entity를 조회합니다."""
    return await mobius_service.get_ae(ae)


@router.post("/ae", summary="AE 생성")
async def create_ae(body: dict = Body(...)):
    """Application Entity를 생성합니다."""
    return await mobius_service.create_ae("", body)


@router.put("/ae/{ae}", summary="AE 수정")
async def update_ae(ae: str, body: dict = Body(...)):
    """Application Entity를 수정합니다."""
    return await mobius_service.update_ae(ae, body)


@router.delete("/ae/{ae}", summary="AE 삭제")
async def delete_ae(ae: str):
    """Application Entity를 삭제합니다."""
    return await mobius_service.delete_ae(ae)


# ==================== Container ====================
@router.get("/ae/{ae}/container/{cnt}", summary="Container 조회")
async def get_container(ae: str, cnt: str):
    """Container를 조회합니다."""
    return await mobius_service.get_container(ae, cnt)


@router.post("/ae/{ae}/container", summary="Container 생성")
async def create_container(ae: str, body: dict = Body(...)):
    """Container를 생성합니다."""
    return await mobius_service.create_container(ae, body)


@router.put("/ae/{ae}/container/{cnt}", summary="Container 수정")
async def update_container(ae: str, cnt: str, body: dict = Body(...)):
    """Container를 수정합니다."""
    return await mobius_service.update_container(ae, cnt, body)


@router.delete("/ae/{ae}/container/{cnt}", summary="Container 삭제")
async def delete_container(ae: str, cnt: str):
    """Container를 삭제합니다."""
    return await mobius_service.delete_container(ae, cnt)


# ==================== ContentInstance (CIN) ====================
@router.get("/ae/{ae}/container/{cnt}/cin/{cin}", summary="CIN 조회")
async def get_cin(ae: str, cnt: str, cin: str = "la"):
    """ContentInstance를 조회합니다. 기본값은 최신(la)."""
    return await mobius_service.get_cin(ae, cnt, cin)


@router.get("/ae/{ae}/container/{cnt}/cin", summary="최신 CIN 조회")
async def get_latest_cin(ae: str, cnt: str):
    """최신 ContentInstance를 조회합니다."""
    return await mobius_service.get_cin(ae, cnt, "la")


@router.post("/ae/{ae}/container/{cnt}/cin", summary="CIN 생성")
async def create_cin(ae: str, cnt: str, body: dict = Body(...)):
    """ContentInstance를 생성합니다."""
    return await mobius_service.create_cin(ae, cnt, body)


# ==================== Subscription ====================
@router.get("/ae/{ae}/container/{cnt}/subscription/{sub}", summary="Subscription 조회")
async def get_subscription(ae: str, cnt: str, sub: str):
    """Subscription을 조회합니다."""
    return await mobius_service.get_subscription(ae, cnt, sub)


@router.post("/ae/{ae}/container/{cnt}/subscription", summary="Subscription 생성")
async def create_subscription(ae: str, cnt: str, body: dict = Body(...)):
    """Subscription을 생성합니다."""
    return await mobius_service.create_subscription(ae, cnt, body)


@router.delete("/ae/{ae}/container/{cnt}/subscription/{sub}", summary="Subscription 삭제")
async def delete_subscription(ae: str, cnt: str, sub: str):
    """Subscription을 삭제합니다."""
    return await mobius_service.delete_subscription(ae, cnt, sub)


# ==================== Group ====================
@router.get("/ae/{ae}/group/{grp}", summary="Group 조회")
async def get_group(ae: str, grp: str):
    """Group을 조회합니다."""
    return await mobius_service.get_group(ae, grp)


@router.post("/ae/{ae}/group", summary="Group 생성")
async def create_group(ae: str, body: dict = Body(...)):
    """Group을 생성합니다."""
    return await mobius_service.create_group(ae, body)


@router.delete("/ae/{ae}/group/{grp}", summary="Group 삭제")
async def delete_group(ae: str, grp: str):
    """Group을 삭제합니다."""
    return await mobius_service.delete_group(ae, grp)
