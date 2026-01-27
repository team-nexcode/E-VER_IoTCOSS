"""
MQTT 서비스 모듈
IoT 디바이스와의 MQTT 통신을 관리합니다.
"""

import asyncio
import json
import logging
from typing import Callable, Optional

import aiomqtt

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class MQTTService:
    """
    MQTT 클라이언트 서비스 클래스
    디바이스와의 MQTT 메시지 송수신을 관리합니다.
    """

    def __init__(self):
        self._client: Optional[aiomqtt.Client] = None
        self._is_connected: bool = False
        self._message_handler: Optional[Callable] = None

    @property
    def is_connected(self) -> bool:
        """MQTT 브로커 연결 상태를 반환합니다."""
        return self._is_connected

    async def connect(self) -> None:
        """
        MQTT 브로커에 연결합니다.
        연결 실패 시 로그를 남기고 재시도합니다.
        """
        try:
            self._client = aiomqtt.Client(
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
            )
            await self._client.__aenter__()
            self._is_connected = True
            logger.info(f"MQTT 브로커 연결 성공: {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
        except Exception as e:
            self._is_connected = False
            logger.error(f"MQTT 브로커 연결 실패: {e}")

    async def disconnect(self) -> None:
        """MQTT 브로커 연결을 종료합니다."""
        if self._client and self._is_connected:
            try:
                await self._client.__aexit__(None, None, None)
                self._is_connected = False
                logger.info("MQTT 브로커 연결 종료")
            except Exception as e:
                logger.error(f"MQTT 브로커 연결 종료 실패: {e}")

    async def subscribe(self, topic: str) -> None:
        """
        특정 MQTT 토픽을 구독합니다.

        Args:
            topic: 구독할 MQTT 토픽 (예: "iotcoss/device/+/status")
        """
        if not self._client or not self._is_connected:
            logger.warning("MQTT 클라이언트가 연결되지 않았습니다. 구독 불가.")
            return

        try:
            await self._client.subscribe(topic)
            logger.info(f"MQTT 토픽 구독: {topic}")
        except Exception as e:
            logger.error(f"MQTT 토픽 구독 실패 ({topic}): {e}")

    async def publish(self, topic: str, payload: dict) -> None:
        """
        MQTT 토픽에 메시지를 발행합니다.

        Args:
            topic: 발행할 MQTT 토픽
            payload: 전송할 데이터 (dict → JSON 변환)
        """
        if not self._client or not self._is_connected:
            logger.warning("MQTT 클라이언트가 연결되지 않았습니다. 발행 불가.")
            return

        try:
            message = json.dumps(payload)
            await self._client.publish(topic, message)
            logger.info(f"MQTT 메시지 발행: {topic} → {message}")
        except Exception as e:
            logger.error(f"MQTT 메시지 발행 실패 ({topic}): {e}")

    def set_message_handler(self, handler: Callable) -> None:
        """
        수신 메시지 핸들러를 설정합니다.

        Args:
            handler: 메시지 수신 시 호출될 콜백 함수
        """
        self._message_handler = handler

    async def listen(self) -> None:
        """
        구독된 토픽의 메시지를 수신하고 핸들러를 호출합니다.
        이 메서드는 블로킹 루프로 동작합니다.
        """
        if not self._client or not self._is_connected:
            logger.warning("MQTT 클라이언트가 연결되지 않았습니다. 리스닝 불가.")
            return

        try:
            async for message in self._client.messages:
                topic = str(message.topic)
                payload = json.loads(message.payload.decode())
                logger.debug(f"MQTT 메시지 수신: {topic} → {payload}")

                if self._message_handler:
                    await self._message_handler(topic, payload)
        except Exception as e:
            logger.error(f"MQTT 메시지 수신 오류: {e}")
            self._is_connected = False


# 전역 MQTT 서비스 인스턴스
mqtt_service = MQTTService()
