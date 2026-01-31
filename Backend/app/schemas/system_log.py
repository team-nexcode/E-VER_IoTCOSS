"""
시스템 로그 Pydantic 스키마
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class SystemLogResponse(BaseModel):
    id: int
    timestamp: datetime
    type: str
    level: str
    source: str
    message: str
    detail: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class SystemLogListResponse(BaseModel):
    items: list[SystemLogResponse]
    total: int
    page: int
    size: int

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
