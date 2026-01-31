"""
모델 패키지 초기화
모든 SQLAlchemy 모델을 import하여 Alembic이 자동으로 감지할 수 있도록 합니다.
"""

from app.models.device import Device
from app.models.power_log import PowerLog
from app.models.user import User
from app.models.api_log import ApiLog
from app.models.system_log import SystemLog

__all__ = ["Device", "PowerLog", "User", "ApiLog", "SystemLog"]
