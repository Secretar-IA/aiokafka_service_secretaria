import asyncio
import json
import logging
from typing import Dict, Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError, KafkaConnectionError

logger = logging.getLogger(__name__)


class KafkaProducer:

    def __init__(self, topic, port, servers) -> None:
        self._topic = topic
        self._port = port
        self._servers = servers
        self.aioproducer = self.create_kafka()

    def create_kafka(self):
        try:
            return AIOKafkaProducer(
                bootstrap_servers=f"{self._servers}:{self._port}",
                value_serializer=self.value_serializer,
            )
        except Exception as error:
            logger.error(
                f"[KafkaProducer] error while creating producer instance {error}"
            )

    def value_serializer(self, value):
        return json.dumps(value).encode("utf-8")

    async def connect_kafka(self):
        try:
            await self.aioproducer.start()
        except KafkaConnectionError as error:
            logger.error(
                f"[KafkaProducer] Kafka may not be yet available with error: {error}, retrying in 10s"
            )
            await asyncio.sleep(10)
            raise KafkaConnectionError
        except KafkaError as error:
            logger.error(
                f"[KafkaProducer] Kafka may not be yet available with error: {error}, retrying in 10s"
            )
            await asyncio.sleep(10)
            raise KafkaError
        except Exception as error:
            print(f"[KafkaProducer] Unknown exception: {error}, retrying in 10s")
            await asyncio.sleep(10)
            raise Exception
        else:
            logger.info(
                f"[KafkaProducer] connected to kafka producer with topic {self._topic}"
            )

    async def send(self, message_value: Dict[str, Any]) -> None:
        try:
            producer_topic_name = self._topic
            outbound_message = {
                "producer": f"{producer_topic_name}_producer",
                "message": message_value,
            }
            logger.info(f"[KafkaProducer] sending outbound message: {outbound_message}")
            await self.aioproducer.send_and_wait(producer_topic_name, outbound_message)
        except Exception as e:
            await self.aioproducer.stop()
            raise e
