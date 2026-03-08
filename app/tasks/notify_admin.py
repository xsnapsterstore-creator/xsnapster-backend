import dramatiq

from db.session import get_db_session
from utils.order import get_order_by_id
from services.email_service import send_admin_order_notification
from core.config import settings


@dramatiq.actor(queue_name="admin", max_retries=5)
def notify_admin(order_id: int):

    db = get_db_session()

    try:
        order = get_order_by_id(order_id, db)

        if not order:
            return

        if order.admin_notified:
            return

        send_admin_order_notification(
            settings.ADMIN_EMAIL,
            settings.ORDER_MAIL,
            order
        )

        order.admin_notified = True
        db.commit()

    finally:
        db.close()