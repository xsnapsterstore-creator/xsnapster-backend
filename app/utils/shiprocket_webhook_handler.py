import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.order import Order
from schemas.payment import OrderStatus

logger = logging.getLogger(__name__)


_STATUS_RANK = {
    OrderStatus.CREATED: 1,
    OrderStatus.CONFIRMED: 2,
    OrderStatus.SHIPPED: 3,
    OrderStatus.FULFILLED: 4,
    OrderStatus.CANCELLED: 99,
}


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().upper()


def _is_newer_status(current: OrderStatus, incoming: OrderStatus) -> bool:
    if current == OrderStatus.CANCELLED:
        return False
    return _STATUS_RANK[incoming] > _STATUS_RANK[current]


def _derive_order_status(event: dict) -> Optional[OrderStatus]:
    current_status = _normalize(event.get("current_status"))
    shipment_status = _normalize(event.get("shipment_status"))

    if "DELIVERED" in current_status or "DELIVERED" in shipment_status:
        return OrderStatus.FULFILLED

    shipping_keywords = (
        "PICKED UP",
        "IN TRANSIT",
        "OUT FOR DELIVERY",
        "ARRIVED",
        "CONNECTED",
        "DISPATCH",
    )

    if any(keyword in current_status for keyword in shipping_keywords):
        return OrderStatus.SHIPPED

    if any(keyword in shipment_status for keyword in shipping_keywords):
        return OrderStatus.SHIPPED

    scans = event.get("scans") or []
    for scan in scans:
        activity = _normalize(scan.get("activity"))
        if "DELIVERED" in activity:
            return OrderStatus.FULFILLED
        if any(keyword in activity for keyword in shipping_keywords):
            return OrderStatus.SHIPPED

    return None


def _find_order_for_event(event: dict, db: Session) -> Optional[Order]:
    channel_order_id = str(event.get("channel_order_id") or "").strip()
    if channel_order_id.isdigit():
        order = db.query(Order).filter(Order.id == int(channel_order_id)).first()
        if order:
            return order

    shiprocket_order_id = str(event.get("order_id") or "").strip()
    if shiprocket_order_id:
        return db.query(Order).filter(Order.shiprocket_order_id == shiprocket_order_id).first()

    return None


def handle_shiprocket_event(event: dict, db: Session):
    order = _find_order_for_event(event, db)
    if not order:
        logger.warning("Shiprocket webhook: no matching order found", extra={"event": event})
        return

    shiprocket_order_id = str(event.get("order_id") or "").strip()
    if shiprocket_order_id and not order.shiprocket_order_id:
        order.shiprocket_order_id = shiprocket_order_id

    awb = event.get("awb")
    if awb is not None:
        order.awb_code = str(awb).strip() or None

    courier_name = str(event.get("courier_name") or "").strip()
    if courier_name:
        order.courier_name = courier_name

    next_status = _derive_order_status(event)
    if next_status and _is_newer_status(order.order_status, next_status):
        order.order_status = next_status

    if next_status in (OrderStatus.SHIPPED, OrderStatus.FULFILLED):
        order.pickup_scheduled = True

    db.commit()
