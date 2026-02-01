"""
Mobius (oneM2M) API 클라이언트 서비스
httpx.AsyncClient를 사용하여 Mobius 서버와 통신하고, 모든 요청/응답을 DB에 로깅합니다.
"""

import json
import logging
import time
from typing import Any, Optional

import httpx
from sqlalchemy import text

from app.config import get_settings
from app.database import async_session
from app.models.api_log import ApiLog

logger = logging.getLogger(__name__)
settings = get_settings()


class MobiusService:
    """Mobius oneM2M 서버 API 클라이언트"""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=settings.mobius_base_url,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """HTTP 클라이언트 종료"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _build_headers(self, operation: str = "retrieve") -> dict[str, str]:
        """
        공통 헤더 생성
        - 생성(create): X-M2M-Origin = SOrigin_nexcode
        - 조회/수정/삭제: X-M2M-Origin = SOrigin_nexcode
        """
        origin = "SOrigin_nexcode"  # MQTT 토픽과 동일한 Origin 사용
        headers = {
            "Accept": "application/json",
            "X-M2M-RI": 12345,
            "X-M2M-Origin": origin,
            "X-API-KEY": settings.X_API_KEY,
            "X-AUTH-CUSTOM-LECTURE": settings.X_AUTH_CUSTOM_LECTURE,
            "X-AUTH-CUSTOM-CREATOR": settings.X_AUTH_CUSTOM_CREATOR,
        }
        if operation == "create":
            headers["Content-Type"] = "application/json;ty=4"  # ty=4: ContentInstance
        else:
            headers["Content-Type"] = "application/json"
        return headers

    def _mask_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """로그 저장 시 민감 정보 마스킹"""
        masked = dict(headers)
        if "X-API-KEY" in masked:
            val = masked["X-API-KEY"]
            masked["X-API-KEY"] = val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
        return masked

    async def _log_to_db(
        self,
        method: str,
        url: str,
        request_headers: dict,
        request_body: Any,
        response_status: Optional[int],
        response_body: Any,
        duration_ms: float,
        direction: str = "outbound",
    ):
        """API 통신 로그를 DB에 저장"""
        try:
            masked_headers = self._mask_headers(request_headers)
            log_entry = ApiLog(
                method=method.upper(),
                url=str(url),
                request_headers=json.dumps(masked_headers, ensure_ascii=False),
                request_body=json.dumps(request_body, ensure_ascii=False) if request_body else None,
                response_status=response_status,
                response_body=json.dumps(response_body, ensure_ascii=False) if response_body else None,
                duration_ms=round(duration_ms, 2),
                direction=direction,
            )
            async with async_session() as session:
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            logger.error(f"API 로그 저장 실패: {e}")

    async def _request(
        self,
        method: str,
        path: str,
        operation: str = "retrieve",
        body: Any = None,
        content_type_suffix: str | None = None,
    ) -> dict[str, Any]:
        """
        공통 HTTP 요청 실행
        - 타이밍 측정
        - DB 로깅
        - 응답 반환
        """
        headers = self._build_headers(operation)
        if content_type_suffix:
            headers["Content-Type"] = f"application/json;ty={content_type_suffix}"

        url = path if path.startswith("http") else path
        start = time.monotonic()
        response_status = None
        response_body = None

        try:
            response = await self.client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=body,
            )
            elapsed = (time.monotonic() - start) * 1000
            response_status = response.status_code
            try:
                response_body = response.json()
            except Exception:
                response_body = response.text

            await self._log_to_db(
                method=method,
                url=str(response.url),
                request_headers=headers,
                request_body=body,
                response_status=response_status,
                response_body=response_body,
                duration_ms=elapsed,
            )

            return {
                "status": response_status,
                "body": response_body,
                "duration_ms": round(elapsed, 2),
            }

        except httpx.HTTPError as e:
            elapsed = (time.monotonic() - start) * 1000
            await self._log_to_db(
                method=method,
                url=str(self.client.base_url) + url,
                request_headers=headers,
                request_body=body,
                response_status=None,
                response_body={"error": str(e)},
                duration_ms=elapsed,
            )
            raise

    # ==================== CSE ====================
    async def get_cse(self) -> dict:
        """CSE 기본 정보 조회"""
        return await self._request("GET", "/")

    # ==================== AE (Application Entity) ====================
    async def get_ae(self, ae: str) -> dict:
        """AE 조회"""
        return await self._request("GET", f"/{ae}")

    async def create_ae(self, ae_name: str, body: dict) -> dict:
        """AE 생성"""
        return await self._request("POST", "/", operation="create", body=body, content_type_suffix="2")

    async def update_ae(self, ae: str, body: dict) -> dict:
        """AE 수정"""
        return await self._request("PUT", f"/{ae}", operation="update", body=body)

    async def delete_ae(self, ae: str) -> dict:
        """AE 삭제"""
        return await self._request("DELETE", f"/{ae}", operation="delete")

    # ==================== Container ====================
    async def get_container(self, ae: str, cnt: str) -> dict:
        """Container 조회"""
        return await self._request("GET", f"/{ae}/{cnt}")

    async def create_container(self, ae: str, body: dict) -> dict:
        """Container 생성"""
        return await self._request("POST", f"/{ae}", operation="create", body=body, content_type_suffix="3")

    async def update_container(self, ae: str, cnt: str, body: dict) -> dict:
        """Container 수정"""
        return await self._request("PUT", f"/{ae}/{cnt}", operation="update", body=body)

    async def delete_container(self, ae: str, cnt: str) -> dict:
        """Container 삭제"""
        return await self._request("DELETE", f"/{ae}/{cnt}", operation="delete")

    # ==================== ContentInstance (CIN) ====================
    async def get_cin(self, ae: str, cnt: str, cin: str = "la") -> dict:
        """ContentInstance 조회 (기본: 최신)"""
        return await self._request("GET", f"/{ae}/{cnt}/{cin}")

    async def create_cin(self, ae: str, cnt: str, body: dict) -> dict:
        """ContentInstance 생성"""
        return await self._request("POST", f"/{ae}/{cnt}", operation="create", body=body, content_type_suffix="4")

    # ==================== Subscription ====================
    async def get_subscription(self, ae: str, cnt: str, sub: str) -> dict:
        """Subscription 조회"""
        return await self._request("GET", f"/{ae}/{cnt}/{sub}")

    async def create_subscription(self, ae: str, cnt: str, body: dict) -> dict:
        """Subscription 생성"""
        return await self._request("POST", f"/{ae}/{cnt}", operation="create", body=body, content_type_suffix="23")

    async def delete_subscription(self, ae: str, cnt: str, sub: str) -> dict:
        """Subscription 삭제"""
        return await self._request("DELETE", f"/{ae}/{cnt}/{sub}", operation="delete")

    # ==================== Group ====================
    async def get_group(self, ae: str, grp: str) -> dict:
        """Group 조회"""
        return await self._request("GET", f"/{ae}/{grp}")

    async def create_group(self, ae: str, body: dict) -> dict:
        """Group 생성"""
        return await self._request("POST", f"/{ae}", operation="create", body=body, content_type_suffix="9")

    async def delete_group(self, ae: str, grp: str) -> dict:
        """Group 삭제"""
        return await self._request("DELETE", f"/{ae}/{grp}", operation="delete")


# 모듈 레벨 싱글톤
mobius_service = MobiusService()
