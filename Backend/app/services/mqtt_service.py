"""
MQTT 서비스 모듈
IoT 디바이스와의 MQTT 통신을 관리합니다.
oneM2M 요청 메시지 수신 시 응답(ACK)을 자동 발송합니다.
"""

import asyncio
import json
import logging
from typing import Callable, Optional

import aiomqtt

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

RECONNECT_DELAY = 5


class MQTTService:
    """MQTT 클라이언트 서비스 클래스"""

    def __init__(self):
        self._client: Optional[aiomqtt.Client] = None
        self._is_connected: bool = False
        self._message_handler: Optional[Callable] = None
        self._subscribed_topic: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    async def connect(self) -> None:
        """MQTT 브로커에 연결합니다."""
        try:
            self._client = aiomqtt.Client(
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
                keepalive=30,
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
        """특정 MQTT 토픽을 구독합니다."""
        if not self._client or not self._is_connected:
            logger.warning("MQTT 클라이언트가 연결되지 않았습니다. 구독 불가.")
            return
        try:
            await self._client.subscribe(topic)
            self._subscribed_topic = topic
            logger.info(f"MQTT 토픽 구독: {topic}")
        except Exception as e:
            logger.error(f"MQTT 토픽 구독 실패 ({topic}): {e}")

    async def publish(self, topic: str, payload: str) -> None:
        """MQTT 토픽에 메시지를 발행합니다."""
        if not self._client or not self._is_connected:
            logger.warning("MQTT 클라이언트가 연결되지 않았습니다. 발행 불가.")
            return
        try:
            await self._client.publish(topic, payload)
            logger.debug(f"MQTT 발행: {topic}")
        except Exception as e:
            logger.error(f"MQTT 발행 실패 ({topic}): {e}")

    def set_message_handler(self, handler: Callable) -> None:
        self._message_handler = handler

    async def _send_onem2m_response(self, topic: str, payload) -> None:
        """
        oneM2M 요청에 대한 응답(ACK)을 발송합니다.
        요청 토픽: /oneM2M/req/{from}/{to}/...
        응답 토픽: /oneM2M/resp/{from}/{to}/...
        """
        if not isinstance(payload, dict):
            return

        rqi = payload.get("rqi") or payload.get("m2m:rqp", {}).get("rqi")
        if not rqi:
            return

        # 요청 토픽에서 응답 토픽 생성
        resp_topic = topic.replace("/oneM2M/req/", "/oneM2M/resp/", 1)

        # 응답 메시지 구성
        response = {
            "rsc": 2000,
            "rqi": rqi,
            "pc": {},
        }

        try:
            await self.publish(resp_topic, json.dumps(response))
            logger.info(f"oneM2M ACK 발송: {resp_topic} (rqi={rqi})")
        except Exception as e:
            logger.error(f"oneM2M ACK 발송 실패: {e}")

    async def listen(self) -> None:
        """
        구독된 토픽의 메시지를 수신하고 핸들러를 호출합니다.
        oneM2M 요청에는 자동으로 응답을 보냅니다.
        연결이 끊기면 자동으로 재연결합니다.
        """
        while True:
            try:
                if not self._client or not self._is_connected:
                    logger.info("MQTT 재연결 시도...")
                    await self.connect()
                    if self._is_connected and self._subscribed_topic:
                        await self.subscribe(self._subscribed_topic)

                if not self._client or not self._is_connected:
                    logger.warning(f"MQTT 연결 실패, {RECONNECT_DELAY}초 후 재시도...")
                    await asyncio.sleep(RECONNECT_DELAY)
                    continue

                async for message in self._client.messages:
                    topic = str(message.topic)
                    try:
                        payload = json.loads(message.payload.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        payload = message.payload.decode(errors="replace")

                    logger.debug(f"MQTT 수신: {topic}")

                    # oneM2M 요청이면 ACK 응답
                    if "/oneM2M/req/" in topic:
                        await self._send_onem2m_response(topic, payload)

                    if self._message_handler:
                        await self._message_handler(topic, payload)

            except asyncio.CancelledError:
                logger.info("MQTT 리스너 종료 요청")
                break
            except Exception as e:
                self._is_connected = False
                logger.error(f"MQTT 연결 끊김: {e}, {RECONNECT_DELAY}초 후 재연결...")
                await asyncio.sleep(RECONNECT_DELAY)


mqtt_service = MQTTService()
