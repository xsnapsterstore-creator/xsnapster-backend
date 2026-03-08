import dramatiq
import logging

from db.session import get_db_session
from services.order_service import OrderFulfillmentService


logger = logging.getLogger(__name__)


@dramatiq.actor(queue_name="order_fulfillment", max_retries=5)
def process_confirmed_order(order_id: int):
    """
    Dramatiq worker responsible for completing post-payment order tasks:
    - Invoice generation
    - Invoice upload to S3
    - Sending confirmation email
    """

    db = get_db_session()

    try:
        OrderFulfillmentService.process_confirmed_order(
            order_id=order_id,
            db=db
        )

    except Exception as e:
        logger.exception(f"Order fulfillment failed for order {order_id}")
        raise e  # allow Dramatiq retry

    finally:
        db.close()