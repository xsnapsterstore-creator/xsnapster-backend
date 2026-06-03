import dramatiq
import logging
from datetime import datetime

from db.session import get_db_session
from models.order import Order
from core.config import settings
from services.shiprocket_service import ShiprocketService

logger = logging.getLogger(__name__)

# Default weight per item in kg (update based on your products)
DEFAULT_ITEM_WEIGHT = 0.5
DEFAULT_LENGTH = 50 # cm
DEFAULT_BREADTH = 35  # cm
DEFAULT_HEIGHT = 5   # cm


def build_shiprocket_order_payload(order: Order) -> dict:
    """
    Build the Shiprocket order payload from an Order model.
    """
    # Build order items for Shiprocket
    order_items = []
    total_weight = 0.0
    
    for item in order.items:
        item_weight = DEFAULT_ITEM_WEIGHT * item.quantity
        total_weight += item_weight
        
        order_items.append({
            "name": item.product.title if item.product else f"Product #{item.product_id}",
            "sku": f"SKU-{item.product_id}-{item.dimension}",
            "units": item.quantity,
            "selling_price": str(item.price),
            "discount": "0",
            "tax": "0",
            "hsn": ""  # Add HSN code if available
        })
    
    # Determine payment mode
    is_cod = order.payment.payment_method == "COD" if order.payment else False
    
    # Shiprocket expects sub_total before discount; it applies total_discount separately.
    items_subtotal = float(
        order.subtotal_before_coupon
        if order.subtotal_before_coupon is not None
        else (order.items_subtotal or 0)
    )
    coupon_discount = float(order.coupon_discount_amount or 0)
    shipping_charges = float(order.delivery_charge or 0)

    # Build the payload
    payload = {
        "order_id": str(order.id),
        "order_date": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else datetime.now().strftime("%Y-%m-%d %H:%M"),
        "pickup_location": "work",  # Your Shiprocket pickup location name
        "channel_id": "",  # Optional: your Shiprocket channel ID
        "comment": f"Order #{order.id}",
        
        # Billing/Shipping address (same for now)
        "billing_customer_name": order.delivery_name,
        "billing_last_name": "",
        "billing_address": order.delivery_address_line,
        "billing_address_2": "",
        "billing_city": order.delivery_city,
        "billing_pincode": order.delivery_zip_code,
        "billing_state": order.delivery_state,
        "billing_country": "India",
        "billing_email": order.user.email if order.user else "",
        "billing_phone": order.delivery_phone_number,
        
        "shipping_is_billing": True,
        "shipping_customer_name": order.delivery_name,
        "shipping_last_name": "",
        "shipping_address": order.delivery_address_line,
        "shipping_address_2": "",
        "shipping_city": order.delivery_city,
        "shipping_pincode": order.delivery_zip_code,
        "shipping_state": order.delivery_state,
        "shipping_country": "India",
        "shipping_email": order.user.email if order.user else "",
        "shipping_phone": order.delivery_phone_number,
        
        # Order details
        "order_items": order_items,
        "payment_method": "COD" if is_cod else "Prepaid",
        "shipping_charges": shipping_charges,
        "giftwrap_charges": 0,
        "transaction_charges": 0,
        "total_discount": coupon_discount,
        "sub_total": items_subtotal,
        
        # Package dimensions
        "length": DEFAULT_LENGTH,
        "breadth": DEFAULT_BREADTH,
        "height": DEFAULT_HEIGHT,
        "weight": round(total_weight, 2) if total_weight > 0 else DEFAULT_ITEM_WEIGHT,
    }
    
    return payload


@dramatiq.actor(queue_name="shiprocket", max_retries=5, min_backoff=30000, max_backoff=300000)
def create_shiprocket_order(order_id: int):
    """
    Dramatiq worker to create an order in Shiprocket.
    
    Features:
    - Idempotency: Skips if shiprocket_order_id already exists
    - Automatic retries with exponential backoff
    - Proper error logging for monitoring
    """
    import asyncio
    
    db = get_db_session()
    
    try:
        # Lock the order for update
        order = (
            db.query(Order)
            .filter(Order.id == order_id)
            .with_for_update()
            .first()
        )
        
        if not order:
            logger.warning(f"[Shiprocket] Order {order_id} not found")
            return
        
        # Idempotency check - skip if already created
        if order.shiprocket_order_id:
            logger.info(f"[Shiprocket] Order {order_id} already has Shiprocket order: {order.shiprocket_order_id}")
            return
        
        # Check serviceability flag
        if not order.serviceable:
            logger.warning(f"[Shiprocket] Order {order_id} marked as not serviceable, skipping")
            return
        
        # Build the Shiprocket payload
        payload = build_shiprocket_order_payload(order)
        
        # Create Shiprocket service and authenticate
        shiprocket = ShiprocketService(
            email=settings.SHIPROCKET_EMAIL,
            password=settings.SHIPROCKET_PASSWORD
        )
        
        # Run async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Authenticate
            loop.run_until_complete(shiprocket.authenticate())
            
            # Create order in Shiprocket
            response = loop.run_until_complete(shiprocket.create_order(payload))
            
            logger.info(f"[Shiprocket] Order {order_id} creation response: {response}")
            
            # Extract Shiprocket order details
            shiprocket_order_id = response.get("order_id")
            shipment_id = response.get("shipment_id")
            
            if shiprocket_order_id:
                order.shiprocket_order_id = str(shiprocket_order_id)
                
            if shipment_id:
                order.shiprocket_shipment_id = str(shipment_id)
                
                # Optionally auto-assign courier (AWB)
                try:
                    awb_response = loop.run_until_complete(
                        shiprocket.assign_courier(int(shipment_id))
                    )
                    logger.info(f"[Shiprocket] AWB assignment response for order {order_id}: {awb_response}")
                    
                    # Extract AWB and courier info
                    awb_data = awb_response.get("response", {}).get("data", {})
                    if awb_data:
                        order.awb_code = awb_data.get("awb_code")
                        order.courier_name = awb_data.get("courier_name")
                        
                except Exception as awb_error:
                    # AWB assignment can fail if no courier available
                    # This is not critical - can be done manually later
                    logger.warning(f"[Shiprocket] AWB assignment failed for order {order_id}: {awb_error}")
            
            db.commit()
            logger.info(f"[Shiprocket] Successfully created Shiprocket order for order {order_id}")
            
        finally:
            loop.close()
            
    except Exception as e:
        db.rollback()
        logger.exception(f"[Shiprocket] Failed to create Shiprocket order for order {order_id}: {e}")
        raise  # Allow Dramatiq to retry
        
    finally:
        db.close()
