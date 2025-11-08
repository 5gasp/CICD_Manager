import asyncio
from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend
from aux import constants as Constants
from taskiq.schedule_sources import LabelScheduleSource
from taskiq import TaskiqScheduler


broker = AioPikaBroker(
    f'amqp://{Constants.TASKIQ_BROKER_USERNAME}:{Constants.TASKIQ_BROKER_PASSWORD}@{Constants.TASKIQ_BROKER_IP}:{Constants.TASKIQ_BROKER_PORT}')\
    .with_result_backend(
        RedisAsyncResultBackend(
            f"redis://{Constants.TASKIQ_REDIS_BACKEND_IP}:{Constants.TASKIQ_REDIS_BACKEND_PORT}"
        )
    )

#scheduler = TaskiqScheduler(
#    broker=broker,
#    sources=[LabelScheduleSource(broker)],
#)


import tasks.initial_test_validation
import tasks.lcm_engine


