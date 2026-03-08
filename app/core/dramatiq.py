import os
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import Retries, AgeLimit, TimeLimit

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

broker = RedisBroker(
    host=REDIS_HOST,
    port=REDIS_PORT,
)


broker.add_middleware(Retries())
broker.add_middleware(TimeLimit())
broker.add_middleware(AgeLimit())



dramatiq.set_broker(broker)
