import asyncio
from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend
from aux import constants as Constants
from taskiq.schedule_sources import LabelScheduleSource
from taskiq import TaskiqScheduler
import yaml
import os
from aux import startup

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "testing_agents_config.yaml")

startup.load_config()

broker = AioPikaBroker(
    f'amqp://{Constants.TASKIQ_BROKER_USERNAME}:{Constants.TASKIQ_BROKER_PASSWORD}@{Constants.TASKIQ_BROKER_IP}:{Constants.TASKIQ_BROKER_PORT}')\
    .with_result_backend(
        RedisAsyncResultBackend(
            f"redis://{Constants.TASKIQ_REDIS_BACKEND_IP}:{Constants.TASKIQ_REDIS_BACKEND_PORT}"
        )
    )

testing_agents_config = None
with open(config_path, "r") as file:
    testing_agents_config = yaml.safe_load(file)


#scheduler = TaskiqScheduler(
#    broker=broker,
#    sources=[LabelScheduleSource(broker)],
#)


import tasks.initial_test_validation
import tasks.lcm_engine


