import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models.order import Order
from schemas.payment import OrderStatus

from utils.invoice import (
    build_invoice_pdf,
    generate_invoice_number,
)

from services.s3_service import s3_service
from services.email_service import send_order_confirmation_email
from core.config import settings


logger = logging.getLogger(__name__)


class OrderFulfillmentService:

    @staticmethod
    def process_confirmed_order(order_id: int, db: Session) -> None:
        """
        Handles post-payment order fulfillment:
        - Generates invoice
        - Uploads invoice to S3
        - Sends order confirmation email with invoice attached
        """

        try:

            logger.info(f"Starting fulfillment for order {order_id}")

            # ===============================
            # 1️⃣ Lock Order & Validate
            # ===============================
            with db.begin():

                order = (
                    db.query(Order)
                    .filter(Order.id == order_id)
                    .with_for_update()
                    .first()
                )

                if not order:
                    logger.warning(f"Order {order_id} not found")
                    return

                db.refresh(order)

                # Ensure payment success
                if order.order_status != OrderStatus.CONFIRMED:
                    logger.info(f"Order {order_id} not confirmed yet")
                    return

                # Idempotency protection
                if order.invoice_url and order.user_email_sent:
                    logger.info(f"Order {order_id} already fulfilled")
                    return

                # Generate invoice number once
                if not order.invoice_number:
                    order.invoice_number = generate_invoice_number(order.id)

                invoice_number = order.invoice_number

            # Transaction released here

            # ===============================
            # 2️⃣ Generate Invoice PDF
            # ===============================
            order = db.query(Order).filter(Order.id == order_id).first()
            db.refresh(order)

            logger.info(f"Generating invoice PDF for order {order_id}")

            pdf_bytes = build_invoice_pdf(order)

            if not pdf_bytes:
                raise Exception("Generated empty invoice PDF")

            # ===============================
            # 3️⃣ Upload Invoice to S3
            # ===============================
            logger.info(f"Uploading invoice to S3 for order {order_id}")

            invoice_url = s3_service.upload_invoice_pdf(
                pdf_bytes,
                invoice_number
            )

            # ===============================
            # 4️⃣ Send Customer Email
            # ===============================
            if order.user and order.user.email and not order.user_email_sent:


                logger.info(f"Sending confirmation email for order {order_id}")

                send_order_confirmation_email(
                    order.user.email,
                    settings.NOREPLY_MAIL,
                    order=order,
                    invoice_bytes=pdf_bytes
                )

                order.user_email_sent = True

            # ===============================
            # 5️⃣ Persist Results
            # ===============================
            order.invoice_url = invoice_url
            order.invoice_generated = True

            db.add(order)
            db.commit()

            logger.info(f"Order fulfillment completed for order {order_id}")

        except SQLAlchemyError:
            logger.exception(
                f"Database error during fulfillment for order {order_id}"
            )
            raise

        except Exception:
            logger.exception(
                f"Order fulfillment failed for order {order_id}"
            )
            raise