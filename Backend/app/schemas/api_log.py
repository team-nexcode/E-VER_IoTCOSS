"""
API 로그 Pydantic 스키마
API 응답 직렬화를 담당하며, 프론트엔드에 맞춰 camelCase alias를 사용합니다.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiLogResponse(BaseModel):
    """API 로그 응답 스키마"""
    id: int
    timestamp: datetime
    method: str
    url: str
    request_headers: Optional[str] = None
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    duration_ms: Optional[float] = None
    direction: str

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ApiLogListResponse(BaseModel):
    """API 로그 목록 응답 스키마 (페이지네이션)"""
    items: list[ApiLogResponse]
    total: int
    page: int
    size: int

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
