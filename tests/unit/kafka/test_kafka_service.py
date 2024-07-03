from typing import Any, AsyncGenerator, Generator
import pytest
import asyncio
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from aiokafka_manager_service.services.kafka_service import KafkaService
from unittest.mock import MagicMock
from pytest_mock import MockerFixture

from aiokafka_manager_service.kafka_producer import KafkaProducer
from aiokafka_manager_service.kafka_consumer import KafkaConsumer


@pytest_asyncio.fixture()
def mock__start_kafka_producers(mocker: MockerFixture):
    async_mock = AsyncMock()
    mocker.patch(
        "aiokafka_manager_service.services.kafka_service.KafkaService._start_kafka_producers",
        side_effect=async_mock,
    )
    return async_mock


@pytest_asyncio.fixture()
def mock__start_kafka_consumers(mocker: MockerFixture):
    async_mock = AsyncMock()
    mocker.patch(
        "aiokafka_manager_service.services.kafka_service.KafkaService._start_kafka_consumers",
        side_effect=async_mock,
    )
    return async_mock


@pytest_asyncio.fixture()
def mock_kafka_producer_send(mocker: MockerFixture):
    async_mock = AsyncMock()
    mocker.patch(
        "aiokafka_manager_service.services.kafka_service.KafkaProducer.send", side_effect=async_mock
    )
    return async_mock


@pytest.fixture()
def mock_kafka_consumer_consume(mocker: MockerFixture):
    return_value = MagicMock()
    return mocker.patch(
        "aiokafka_manager_service.services.kafka_service.KafkaConsumer.consume",
        return_value=return_value,
    )



class TestKafkaService:

    @pytest.mark.asyncio
    async def test_start_kafka_connections(
        self,
        kafka_service: KafkaService,
        mock__start_kafka_producers: AsyncMock,
        mock__start_kafka_consumers: AsyncMock,
    ):
        env_kafka_producer_topics = "new_audio_topic,"
        producer_topics = [
            i for i in filter(None, env_kafka_producer_topics.split(","))
        ]
        env_kafka_consumer_topics = "audio_response_topic,"
        consumer_topics = [
            i for i in filter(None, env_kafka_consumer_topics.split(","))
        ]
        await kafka_service.start_kafka_connections(producer_topics=producer_topics, consumer_topics=consumer_topics)
        await kafka_service._start_kafka_producers()
        await kafka_service._start_kafka_consumers()
        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_start_kafka_producers(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
    ):
        await kafka_service._start_kafka_producers(["test-topic"])

        assert len(kafka_service.kafka_producers.items())
        assert kafka_service.kafka_producers.get("test-topic")
        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_start_kafka_producers_empty(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
    ):
        await kafka_service._start_kafka_producers([])

        assert not len(kafka_service.kafka_producers.items())

        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_start_kafka_consumers(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
    ):
        await kafka_service._start_kafka_consumers(["test-topic"])
        assert len(kafka_service.kafka_consumers.items())
        assert kafka_service.kafka_consumers.get("test-topic")
        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_start_kafka_consumers_empty(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
    ):
        await kafka_service._start_kafka_consumers([])
        assert not len(kafka_service.kafka_consumers.items())
        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_get_producer_by_topic(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
    ):
        await kafka_service._start_kafka_producers(["test-topic"])

        producer = kafka_service.get_producer_by_topic("test-topic")
        assert producer
        assert producer._topic == "test-topic"
        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_get_consumer_by_topic(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
    ):
        await kafka_service._start_kafka_consumers(["test-topic"])

        consumer = kafka_service.get_consumer_by_topic("test-topic")
        assert consumer
        assert consumer._topic == "test-topic"
        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_send_message_topic(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
        mock_kafka_producer_send,
    ):
        await kafka_service._start_kafka_producers(["test-topic"])
        await kafka_service.send_message_to_topic("test-topic", "message")
        await KafkaProducer.send()
        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_get_consumer_stream_by_topic(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
        mock_kafka_consumer_consume: MagicMock,
    ):
        await kafka_service._start_kafka_consumers(["test-topic"])

        kafka_service.get_consumer_stream_by_topic(topic="test-topic")
        mock_kafka_consumer_consume.assert_called_once()
        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_get_consumer_stream_by_topic_with_message(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
        mock_kafka_consumer_consume: MagicMock,
    ):
        await kafka_service._start_kafka_consumers(["test-topic"])

        stream = kafka_service.get_consumer_stream_by_topic(topic="test-topic")
        mock_kafka_consumer_consume.assert_called_once()
        async for msg in stream:
            assert msg.get("message") == "message"
            break
        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_subscribe_to_consumer_stream(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
    ):
        await kafka_service._start_kafka_producers(["test-topic"])
        await kafka_service._start_kafka_consumers(["test-topic"])
        await kafka_service.send_message_to_topic("test-topic", "message")

        stream = kafka_service.subscribe_to_consumer_stream(topic="test-topic")
        async for msg in stream:
            assert msg.get("message") == "message"
            break
        await kafka_service.stop_kafka_connections()

    @pytest.mark.asyncio
    async def test_subscribe_callback_to_consumer(
        self,
        kafka_service: KafkaService,
        #kafka_container_service,
    ):
        await kafka_service._start_kafka_producers(["test-topic"])
        await kafka_service._start_kafka_consumers(["test-topic"])
        await kafka_service.send_message_to_topic("test-topic", "message")
        consumer = kafka_service.get_consumer_by_topic("test-topic")
        mock_fn = AsyncMock()

        await kafka_service.subscribe_callback_to_consumer(
            topic="test-topic", callback=mock_fn
        )
        mock_fn.assert_called_once_with(consumer)
        await kafka_service.stop_kafka_connections()
