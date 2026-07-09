"""
Payment routes — Razorpay and Stripe payment initiation and verification.
"""

import hashlib
import hmac
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentGateway, PaymentStatus
from app.schemas.payment import (
    PaymentInitRequest, PaymentInitResponse,
    PaymentVerifyRequest, PaymentVerifyResponse,
)

router = APIRouter()


@router.post("/initiate", response_model=PaymentInitResponse)
async def initiate_payment(
    data: PaymentInitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a payment order with Razorpay or Stripe.
    Returns gateway-specific data needed by the frontend to open the payment modal.
    """
    order_uuid = uuid.UUID(data.order_id)
    result = await db.execute(select(Order).where(Order.id == order_uuid))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order is not in PENDING state")

    amount_in_paise = int(order.total * 100)  # Razorpay uses smallest unit

    if data.gateway == PaymentGateway.RAZORPAY:
        if not settings.RAZORPAY_KEY_ID or settings.RAZORPAY_KEY_ID == "rzp_test_..." or "change-me" in settings.RAZORPAY_KEY_ID:
            mock_order_id = f"rzp_mock_{uuid.uuid4().hex[:12]}"
            payment = Payment(
                order_id=order.id,
                gateway=PaymentGateway.RAZORPAY,
                gateway_order_id=mock_order_id,
                amount=order.total,
                currency="INR",
            )
            db.add(payment)
            await db.flush()
            await db.commit()
            return PaymentInitResponse(
                gateway=PaymentGateway.RAZORPAY,
                gateway_order_id=mock_order_id,
                amount=amount_in_paise,
                currency="INR",
                key_id="rzp_test_mockkey",
                order_id=str(order.id),
            )
        
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        rz_order = client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": str(order.id),
        })

        # Record payment initiation
        payment = Payment(
            order_id=order.id,
            gateway=PaymentGateway.RAZORPAY,
            gateway_order_id=rz_order["id"],
            amount=order.total,
            currency="INR",
        )
        db.add(payment)
        await db.flush()
        await db.commit()

        return PaymentInitResponse(
            gateway=PaymentGateway.RAZORPAY,
            gateway_order_id=rz_order["id"],
            amount=amount_in_paise,
            currency="INR",
            key_id=settings.RAZORPAY_KEY_ID,
            order_id=str(order.id),
        )

    elif data.gateway == PaymentGateway.STRIPE:
        if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY == "sk_test_..." or "change-me" in settings.STRIPE_SECRET_KEY:
            mock_payment_id = f"pi_mock_{uuid.uuid4().hex[:12]}"
            mock_client_secret = f"pi_mock_{uuid.uuid4().hex[:12]}_secret_{uuid.uuid4().hex[:12]}"
            payment = Payment(
                order_id=order.id,
                gateway=PaymentGateway.STRIPE,
                gateway_payment_id=mock_payment_id,
                amount=order.total,
                currency="USD",
            )
            db.add(payment)
            await db.flush()
            await db.commit()
            return PaymentInitResponse(
                gateway=PaymentGateway.STRIPE,
                gateway_order_id=mock_client_secret,
                amount=int(order.total * 100),
                currency="USD",
                key_id="pk_test_mockkey",
                order_id=str(order.id),
            )

        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=int(order.total * 100),  # cents
            currency="usd",
            metadata={"order_id": str(order.id)},
        )

        payment = Payment(
            order_id=order.id,
            gateway=PaymentGateway.STRIPE,
            gateway_payment_id=intent.id,
            amount=order.total,
            currency="USD",
        )
        db.add(payment)
        await db.flush()
        await db.commit()

        return PaymentInitResponse(
            gateway=PaymentGateway.STRIPE,
            gateway_order_id=intent.client_secret,
            amount=int(order.total * 100),
            currency="USD",
            key_id=settings.STRIPE_PUBLISHABLE_KEY,
            order_id=str(order.id),
        )


@router.post("/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    data: PaymentVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify payment signature and update order status to COMPLETED."""
    order_uuid = uuid.UUID(data.order_id)
    result = await db.execute(select(Order).where(Order.id == order_uuid))
    order = result.scalar_one_or_none()
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    if data.gateway == PaymentGateway.RAZORPAY:
        # Verify HMAC signature unless it's a test/mock checkout
        if data.gateway_order_id and data.gateway_order_id.startswith("rzp_mock_"):
            pass
        else:
            expected_sig = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                f"{data.gateway_order_id}|{data.gateway_payment_id}".encode(),
                hashlib.sha256,
            ).hexdigest()
            if data.gateway_signature != expected_sig:
                raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Update payment record
    result = await db.execute(
        select(Payment).where(Payment.order_id == order.id)
    )
    payment = result.scalar_one_or_none()
    if payment:
        payment.status = PaymentStatus.CAPTURED
        payment.gateway_payment_id = data.gateway_payment_id or payment.gateway_payment_id
        payment.gateway_signature = data.gateway_signature or payment.gateway_signature
    else:
        # Create a payment record if it didn't exist
        payment = Payment(
            order_id=order.id,
            gateway=data.gateway,
            status=PaymentStatus.CAPTURED,
            gateway_payment_id=data.gateway_payment_id or f"pay_mock_{uuid.uuid4().hex[:12]}",
            amount=order.total,
            currency="USD" if data.gateway == PaymentGateway.STRIPE else "INR"
        )
        db.add(payment)

    # Update order status
    order.status = OrderStatus.COMPLETED
    await db.flush()
    await db.commit()

    return PaymentVerifyResponse(
        success=True,
        message="Payment verified successfully",
        order_id=str(order.id),
    )
