import os
import dramatiq
from dramatiq.brokers.redis import RedisBroker

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

broker = RedisBroker(
    host=REDIS_HOST,
    port=REDIS_PORT,
)

dramatiq.set_broker(broker)
