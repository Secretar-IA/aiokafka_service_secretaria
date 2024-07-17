import pytest
import asyncio

import pytest_asyncio
# from aiokafka_manager_service.kafka_consumer import KafkaConsumer
# from aiokafka_manager_service.kafka_producer import KafkaProducer
from aiokafka_manager_service.services.kafka_service import KafkaService

# from aiohttp import (
#     ClientConnectorError,
#     ClientResponse,
#     ClientSession,
#     ClientWebSocketResponse,
#     WSMessage,
#     WSMsgType,
#     BasicAuth,
# )
import requests
#from aiohttp.client_exceptions import WSServerHandshakeError



# @pytest.fixture(scope="function")
# async def close_connections():
#     # Will be executed before the first test
#     KafkaService()
#     yield
#     # Will be executed after the last test
#     await KafkaService.stop_kafka_connections()

@pytest.fixture
def kafka_service():
    kafka_server = "broker"
    kafka_port = "29092"
    kafka_service = KafkaService(server=kafka_server, port=kafka_port)

    yield kafka_service
    
# async def is_responsive(url):
#     try:
#         client_session = ClientSession()
#         response = await client_session.get(url)
#         if response.status == 200:
#             return True
#     except Exception as e:
#         print(e)
#         return False
#         #return await is_responsive(url)

def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False

#@pytest.fixture(scope="session")
@pytest_asyncio.fixture
async def kafka_container_service(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    kafka_port = 29092
    url = f"http://{docker_ip}:{kafka_port}"
    docker_services.wait_until_responsive(
        timeout=50.0, pause=1, check=is_responsive(url)
    )
    return url

# @pytest.fixture
# def mock_consumer():
#     consumer = KafkaConsumer(topic='test_topic', port=29092, servers='broker')
#     yield consumer

# @pytest.fixture
# def mock_producer():
#     producer = KafkaProducer(topic='test_topic', port=29092, servers='broker')
#     yield producer

# @pytest.fixture
# def event_loop():
#     loop = asyncio.get_event_loop()
#     yield loop
#     loop.close()
