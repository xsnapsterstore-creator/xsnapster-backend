import dramatiq
from core.dramatiq import broker

@dramatiq.actor
def test_task(message: str):
    print(f"[WORKER] received: {message}")
