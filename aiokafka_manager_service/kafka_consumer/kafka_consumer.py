import logging
import json
import asyncio
from typing import Dict, Any

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError, KafkaConnectionError
import logging

# from app.core.producer.kafka_producer import KafkaProducer

logger = logging.getLogger(__name__)


class KafkaConsumer:

    def __init__(self, topic, port, servers) -> None:
        self._topic = topic
        self._port = port
        self._servers = servers
        self.aioconsumer = self.create_kafka()

    def create_kafka(self):
        try:
            return AIOKafkaConsumer(
                self._topic,
                bootstrap_servers=f"{self._servers}:{self._port}",
                value_deserializer=self.value_deserializer,
            )
        except Exception as error:
            logger.error(
                f"[KafkaConsumer] error while creating consumer instance {error}"
            )

    def value_deserializer(self, value):
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"[KafkaConsumer] got malformed json", extra={"error": e})
            return {}

    async def connect_kafka(self):
        try:
            await self.aioconsumer.start()
        except KafkaConnectionError as error:
            logger.error(
                f"[KafkaConsumer] Kafka may not be yet available with error: {error}, retrying in 10s"
            )
            await asyncio.sleep(10)
            return await self.connect_kafka()
        except KafkaError as error:
            logger.error(
                f"[KafkaConsumer] Kafka may not be yet available with error: {error}, retrying in 10s"
            )
            await asyncio.sleep(10)
            return await self.connect_kafka()
        except Exception as error:
            print(f"[KafkaConsumer] Unknown exception: {error}, retrying in 10s")
            await asyncio.sleep(10)
            return await self.connect_kafka()
        else:
            logger.info(
                f"[KafkaConsumer] connected to kafka consumer with topic {self._topic}"
            )

    async def consume(self):
        try:
            logger.info(f"[KafkaConsumer] streaming messages for topic: {self._topic}")
            async for msg in self.aioconsumer:
                yield msg.value
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await self.aioconsumer.stop()
