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

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)




import tasks.workers
import tasks.workers2

async def ticker_loop():
    await broker.startup()
    try:
        while True:
            await heavy_task2.kiq()
            await asyncio.sleep(30)
    finally:
        await broker.shutdown()

if __name__ == "__main__":
    asyncio.run(ticker_loop())


