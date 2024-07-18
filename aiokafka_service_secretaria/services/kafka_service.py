import asyncio
import logging
from typing import Dict, Any, List

from aiokafka_service_secretaria.kafka_consumer import KafkaConsumer
from aiokafka_service_secretaria.kafka_producer import KafkaProducer

logger = logging.getLogger(__name__)


class KafkaService:

    def __init__(self, server, port):
        self.kafka_server = server
        self.kafka_port = port
        self.kafka_producer_topics: List[str] = []
        self.kafka_consumer_topics: List[str] = []
        self.kafka_consumers: Dict[str, KafkaConsumer] = {}
        self.kafka_producers: Dict[str, KafkaProducer] = {}

    async def start_kafka_connections(self, producer_topics: List[str] = [], consumer_topics: List[str] = []):   
        logger.info(
            f"[KafkaService] consumer topics: {consumer_topics}, producer topics: {producer_topics}"
        )
        await self._start_kafka_producers(producer_topics)
        await self._start_kafka_consumers(consumer_topics)

    async def _start_kafka_producers(self, producer_topics: List = []):
        if not len(producer_topics):
            logger.warning(f'[KafkaService] producer topics werent provided')
            return
        for topic in producer_topics:
            if self.kafka_producers.get(topic):
                logger.warning(f'[KafkaService] producer with topic {topic} is already started')
                continue
                
            producer = KafkaProducer(
                topic=topic,
                port=self.kafka_port,
                servers=self.kafka_server,
            )
            self.kafka_producers[topic] = producer

        tasks = []
        for topic, producer in self.kafka_producers.items():
            tasks.append(asyncio.create_task(producer.connect_kafka()))

        await asyncio.gather(*tasks)

    async def _start_kafka_consumers(self, consumer_topics: List = []):
        if not len(consumer_topics):
            logger.warning(f'[KafkaService] consumer topics werent provided')
            return
        for topic in consumer_topics:
            if self.kafka_consumers.get(topic):
                logger.warning(f'[KafkaService] consumer with topic {topic} is already started')
                continue
            consumer = KafkaConsumer(
                topic=topic,
                port=self.kafka_port,
                servers=self.kafka_server,
            )
            
            self.kafka_consumers[topic] = consumer

        tasks = []
        for topic, consumer in self.kafka_consumers.items():
            tasks.append(asyncio.create_task(consumer.connect_kafka()))

        await asyncio.gather(*tasks)

    def get_producer_by_topic(self, topic) -> KafkaProducer:
        if not self.kafka_producers.get(topic):
            return None

        return self.kafka_producers.get(topic)

    def get_consumer_by_topic(self, topic) -> KafkaConsumer:
        if not self.kafka_consumers.get(topic):
            return None

        return self.kafka_consumers.get(topic)

    async def stop_kafka_connections(self):
        await asyncio.gather(self._stop_kafka_producers(), self._stop_kafka_consumers())

    async def _stop_kafka_producers(self):
        tasks = []
        if len(self.kafka_producers.items()):
            for topic, producer in self.kafka_producers.items():
                tasks.append(producer.aioproducer.stop())

        await asyncio.gather(*tasks)
        self.kafka_producers = []

    async def _stop_kafka_consumers(self):
        tasks = []
        if len(self.kafka_consumers.items()):
            for topic, producer in self.kafka_consumers.items():
                tasks.append(producer.aioconsumer.stop())

        await asyncio.gather(*tasks)
        self.kafka_consumers = []

    async def send_message_to_topic(self, topic, message):
        try:
            kafka_producer = self.get_producer_by_topic(topic)
            await asyncio.create_task(kafka_producer.send(message))
        except Exception as e:
            logger.error(
                f"[KafkaService] error while sending message to kafka producer with topic {topic}: {e}"
            )

    async def subscribe_callback_to_consumer(self, topic, callback):
        try:
            consumer = self.get_consumer_by_topic(topic)
            if not consumer:
                logger.warning(
                    f"[KafkaService] could not get kafka consumer with topic: {self.kafka_consumer_topic}"
                )
                await asyncio.sleep(10)
                return await self.subscribe_callback_to_consumer(topic, callback)

            return await callback(consumer)
        except Exception as e:
            logger.error(
                f"[KafkaService] could not stream messages to callback {topic}: {e}"
            )

    async def subscribe_to_consumer_stream(self, topic):
        while True:
            try:
                consumer = self.get_consumer_by_topic(topic)
                if not consumer:
                    logger.warning(
                        f"[KafkaService] could not get kafka consumer with topic: {topic}"
                    )
                    await asyncio.sleep(5)
                    continue

                logger.info(
                    f"[KafkaService] subscribing client to consumer for topic : {topic}"
                )
                try:
                    async for msg in consumer.aioconsumer:
                        yield msg.value
                finally:
                    await consumer.aioconsumer.stop()
            except Exception as e:
                logger.error(f"[KafkaService] unkwnown error: {e}")
                await asyncio.sleep(5)
            finally:
                # Will leave consumer group; perform autocommit if enabled.
                await consumer.aioconsumer.stop()

    def get_consumer_stream_by_topic(self, topic):
        try:
            consumer = self.get_consumer_by_topic(topic)
            logger.info(
                f"[KafkaService] found consumer for topic: {topic} - {consumer}"
            )
            if not consumer:
                logger.warning(
                    f"[KafkaService] could not get kafka consumer with topic: {topic}"
                )
                return self.get_consumer_stream_by_topic(topic)

            return consumer.consume()
        except Exception as e:
            logger.error(f"[KafkaService] unkwnown error: {e}")
